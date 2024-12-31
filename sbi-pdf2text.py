#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import codecs
import logging
import argparse

from os.path import join, exists
from typing import Final, List, cast, Generator, Tuple
from enum import Enum
from dataclasses import dataclass

from pdfminer.high_level import extract_text
from mojimoji import zen_to_han

input_dir: Final[str] = "./input"
output_dir: Final[str] = "./output"

re_date_format = re.compile(r"\d{4}/\d{2}/\d{2}")
logger = logging.getLogger(__name__)


class PdfType(Enum):
    # 「株式等利益剰余金配当金のお知らせ」電子交付のお知らせ
    JAPANESE_STOCK_DIVIDEND_REPORT = 1
    # 「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ
    GLOBAL_STOCK_DIVIDEND_REPORT_VER1 = 2   
    GLOBAL_STOCK_DIVIDEND_REPORT_VER2 = 3   # 2021年4月8日あたりからのフォーマット


def judge_pdf_type(text: str) -> PdfType:

    # 「TWCODE:」で始まっている場合は「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ と判断
    if text.lstrip().startswith("TWCODE:"):
        for line in text.splitlines():
            if "外国株式等　配当金等のご案内" in line:
                return PdfType.GLOBAL_STOCK_DIVIDEND_REPORT_VER1
        return PdfType.GLOBAL_STOCK_DIVIDEND_REPORT_VER2

    for line in text.splitlines():
        if "株式等配当金のお知らせ" in line:
            return PdfType.JAPANESE_STOCK_DIVIDEND_REPORT

    raise NotImplementedError()


def parse_japanese_stock_dividend_report(text: str) -> Generator[List[str], None, None]:
    """『「株式等利益剰余金配当金のお知らせ」電子交付のお知らせ』PDFを解析して、情報を抽出。

    ・銘柄名： df.loc[3][0] または df.loc[8][0]。情報がない場合は、「以下余白」が入る。
    ・お支払日： df.loc[3][4] または df.loc[8][4]。全角文字列。年月が1桁の場合、全角空白が入る。
    ・配当単価（円）： df.loc[3][8] または df.loc[8][8]。全角文字列。
    ・数量（株数・口数）： df.loc[3][12] または df.loc[8][12]。全角文字列。
    ・配当金額（税引前）（円）： df.loc[5][0] または df.loc[10][0]。全角文字列。
    ・所得税（円）： df.loc[5][2] または df.loc[10][2]。全角文字列。
    ・地方税（円）： df.loc[5][3] または df.loc[10][3]。全角文字列。
    ・端数処理代金（円）： df.loc[5][8] または df.loc[10][8]。全角文字列。
    ・お受取金額（円）： df.loc[5][12] または df.loc[10][12]。全角文字列。

    Args:
        text: pdfminerのextract_textの返却値
    """

    def count_page(lines: List[str]) -> int:
        """ページ数をカウント。
        
        各ページに「株式等配当金のお知らせ」が記載されているので、それをカウントする。

        Args:
            lines: pdfminerのextract_textの返却値

        Returns:
            int: ページ数
        """
        page = 0
        for line in lines:
            if "株式等配当金のお知らせ" in line:
                page += 1
        return page

    def search_start_index(lines: List[str], start_pos: int = 0) -> Tuple[int, int]:
        """銘柄の開始位置を検索

        - 1ページ内には最大で2銘柄が記載される。
        - 

        Args:
            lines: pdfminerのextract_textの返却値
            start_pos: 検索開始位置

        Returns:
            Tuple[銘柄1の開始位置, 銘柄2の開始位置]

            銘柄がない場合は、開始位置は-1となる。
        """
        stock1_start = -1
        stock2_start = -1

        for i in range(start_pos, len(lines)):
            line = lines[i]

            if "株式等配当金のお知らせ" in line:
                # [銘柄1] 4行前に銘柄名の記載がある
                stock1_start = i - 4

                # 銘柄と銘柄コードの間に空行がない場合の対応
                # 空行の追加は別途行うがここでは開始位置を調整する。
                if lines[i - 3] != "":
                    stock1_start = i - 3

                # [銘柄2] 19行後に銘柄名の記載がある
                stock2_start = i + 19
            
            # 「以下余白」が含まれている場合は銘柄2の開始位置を-1にする
            if "以下余白" in line:
                stock2_start = -1

            if "端数処理代金につきまして" in line or "（取引店）" in line:
                break

        return (stock1_start, stock2_start)


    def parse_data(lines: List[str]) -> List[str]:
        """文字文字列配列を解析して、対象銘柄の配当金情報を抽出

        1銘柄目と2銘柄目でデータ構造が異なるが、呼び出し元で同じ構造にして呼び出す前提とする。
        全角数字は半角数字に変換する。

        サンプルデータ(14行の配列データ)
        ```
        0: 三菱商事
        1: 
        2: （８０５８　　）
        3: 
        4: ２０２３年１２月　１日 　　　　１０５．０００００００ 　　　　　　　　　　　　　　４
        5: 
        6: 　　　　　　　　　　　　４２０ 　　　　　　　　　　　６４ 　　　　　　　　　　　２１
        7: 
        8: 　　　　　　　　　　　　０ 　　　　　　　　　　　　３３５
        9: 
        10: 特定口座配当等受入対象
        11: 
        12: ２０２３年　９月３０日
        13: 
        ```

        Args:
            lines (List[str]): 銘柄の文字列配列。詳細イメージは上記のサンプルデータを参照。

        Returns:
            List[str]: _description_
        """
        assert len(lines) == 14

        data: List[str] = []

        line5 = lines[4].split(" ")
        line7 = lines[6].split(" ")
        line9 = lines[8].split(" ")

        try:
            # 銘柄名
            data.append(lines[0].strip())
            # 銘柄コード
            data.append(zen_to_han(lines[2].strip().replace("　", "").replace("（", "").replace("）", "").replace("\u3000", "")))
            # お支払日
            data.append(zen_to_han(line5[0].replace("　", "")))
            # 配当単価（円）
            data.append(zen_to_han(line5[1].replace("　", "")).replace(",", ""))
            # 数量（株数・口数）
            data.append(zen_to_han(line5[2].replace("　", "")).replace(",", ""))
            # 配当金額（税引前）
            data.append(zen_to_han(line7[0].replace("　", "")).replace(",", "")) 
            # 所得税（円）
            data.append(zen_to_han(line7[1].replace("　", "")).replace(",", ""))
            # 地方税（円）
            data.append(zen_to_han(line7[2].replace("　", "")).replace(",", ""))
            # 端数処理代金（円）
            data.append(zen_to_han(line9[0].replace("　", "")).replace(",", ""))
            # お受取金額（円）
            data.append(zen_to_han(line9[1].replace("　", "")).replace(",", ""))
        except Exception as e:
            logger.error(f"データ解析エラー: {repr(lines)}")
            for index, line in enumerate(lines):
                logger.info(f"[{index}]: 『{line}』")
            raise e

        return data

    def adjust_lines(lines: List[str], start_index: int) -> int:
        add_line_num = 0

        # 1行目と2行目の間に空行がない場合、空行を追加する
        # データ的には空行が入らない方が少ない。
        if lines[start_index + 1] != "":
            lines.insert(start_index + 1, "")
            add_line_num += 1

        return add_line_num


    lines = text.splitlines()

    total_page = count_page(lines)
    process_page = 0

    next_start_index = 0
    while True:
        (stock1_start, stock2_start) = search_start_index(lines, next_start_index)

        if stock1_start != -1:
            stock2_start += adjust_lines(lines, stock1_start)
            # 5行目から13行目までの情報を除外。4行+10行=14行のデータをparse_dataに渡す（銘柄2と同じ構造）
            yield parse_data(lines[stock1_start:stock1_start+4] + lines[stock1_start+13:stock1_start+23])

            process_page += 1
        else:
            # 銘柄1がない場合は終了
            break

        if stock2_start != -1:
            adjust_lines(lines, stock2_start)
            yield parse_data(lines[stock2_start:stock2_start+14])
            # 次のページの開始位置を設定
            next_start_index = stock2_start + 25
        else:
            # 銘柄2がない場合は最終ページのため終了
            break
    
    if total_page != process_page:
        logger.warning(f"ページ数が一致しません。 実際のページ数:{total_page}, 解析したページ数:{process_page}")
        raise ValueError("ページ数が一致しません。")


def parse_global_stock_dividend_report(text: str, pdf_type: PdfType) -> Generator[List[str], None, None]:
    """『「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ』PDFを解析して、情報を抽出。

        Args:
          text: pdfminerのextract_textの返却値
    """

    def search_start_index(lines: List[str], start_pos: int = 0) -> int:
        for i in range(start_pos, len(lines)):
            line = lines[i].strip()

            # 上から探してYYYY/MM/DDの形式で日付が記載されている最初の行を検索
            if re_date_format.match(line):
                return i

        return -1

    def adjust_lines(lines: List[str], start_index: int) -> int:
        add_line_num = 0
        index = start_index

        # 必要に応じて処理を実装
        for i in range(start_index, start_index + 56):
            line = lines[i]

            if "gT" == line:
                if lines[i+1] == "":
                    del lines[i+1]
                del lines[i]

        return add_line_num
    
    def parse_data_ver1(lines: List[str]) -> List[str]:
        """

        サンプルデータ
        ```
        0: 2019/08/08
        1: 
        2: 現地基準日
        3: 2019/08/02
        4: 
        5: 2019/08/07
        6: 分配通貨
        7: 米国ドル
        8: 
        9: 外国源泉税率（%） 1単位あたり金額
        10: 
        11:           10.0            0.367189
        12: 
        13: 銘柄コード
        14: 304-HYG
        15: 決済方法
        16: 外貨決済
        17: 
        18: iシェアーズ iBoxx USD Hイールド社債 ETF
        19: 円貨決済用レート
        20: 
        21: 口座区分
        22: 
        23: 勘定設定年
        24: 
        25: 備考
        26: 
        27: 銘　柄　名
        28: 
        29: 数量
        30: 
        31: 配当金等金額
        32: 
        33: 外国源泉
        34: 徴収税額
        35: 
        36: 外国手数料
        37: 
        38: 外国精算金額
        39: 
        40: 国内源泉
        41: 徴収税額
        42: 
        43: 国内手数料
        44: 
        45: 消費税
        46: 
        47: 受取金額
        48: 
        49:             28
        50: 
        51:                  10.28
        52: 
        53:                   1.02
        54: 
        55:                   0.00
        56: 
        57:                   9.26
        58: 外貨
        59: 円貨                 
        60: 
        61:                    1.85             0.00
        62: 
        63:                   0.00
        64: 
        65:                   7.41
        66: 
        67: （国内源泉徴収税の明細）
        68: 
        69: 申告レート基準日
        70: 
        71: 為替レート基準日
        72: 2019/08/07
        73: 2019/08/08
        74: 
        75: 申告レート
        76: 為替レート
        77:     105.1700
        78:     106.1100
        79: 
        80: 配当金等金額（円）
        81: 
        82: 外国源泉
        83: 徴収税額（円）
        84: 
        85: 国内課税所得額（円）
        86: 
        87: 所得税
        88: 
        89: 地方税
        90: 
        91: 国内源泉
        92: 徴収税額
        93: 
        94:                  1,081
        95: 
        96:                    107
        97: 
        98:               974
        99: 
        100: 外貨
        101:                   1.40
        102: 円貨              149
        103: 
        104:                   0.45
        105: 
        106:                    1.85
        107:                48                  
        108: 
        109:         ＊＊　 以　　上 　＊＊
        110: 
        111: お客様のお受取金額                  7.41米国ドル
        ```

        """
        assert len(lines) == 112

        data: List[str] = []

        for i, line in enumerate(lines):
            lines[i] = line.strip()

        # 空行をチェック
        for i in [1, 4, 8, 10, 12, 17, 20, 22, 24, 26, 28, 60, 74, 93, 95, 99, 103, 105]:
            if lines[i] != "":
                raise ValueError(f"空行チェックエラー: {i}番目の行に空行がありません。 data={repr(lines)}")
        
        # 数値チェック
        for i in [101]:
            if not re.match(r"\d+\.*\d*", lines[i]):
                raise ValueError(f"数値チェックエラー: {i}番目の行に数値がありません。 data={repr(lines)}")
        
        line12 = re.sub(r"\s+", " ", lines[11]).split(" ")
        line62 = re.sub(r"\s+", " ", lines[61]).split(" ")
        line103 = re.sub(r"\s+", " ", lines[102]).split(" ")

        # 配当金等支払日
        data.append(lines[5])
        # 国内支払日
        data.append(lines[0])
        # 現地基準日
        data.append(lines[3])
        # 銘柄コード
        data.append(lines[14])
        # 銘柄名
        data.append(lines[18])
        # 分配通貨
        data.append("※未取得※")
        # 外国源泉税率（%）
        data.append(line12[0])
        # 1単位あたり金額
        data.append(line12[1])
        # 決済方法
        data.append("※未取得※")
        # 数量
        data.append(lines[49].replace(",", ""))
        # 配当金等金額
        data.append(lines[51].replace(",", ""))
        # 外国源泉徴収税額
        data.append(lines[53].replace(",", ""))
        # 外国手数料
        data.append(lines[55].replace(",", ""))
        # 外国精算金額（外貨）
        data.append(lines[57].replace(",", ""))
        # 国内源泉徴収税額（外貨）
        data.append(line62[0].replace(",", ""))
        # 受取金額
        data.append(lines[65].replace(",", ""))
        # 申告レート基準日
        data.append(lines[72])
        # 申告レート
        data.append(lines[77].replace(",", ""))
        # 為替レート基準日
        data.append(lines[73])
        # 為替レート
        data.append(lines[78].replace(",", ""))
        # 配当金等金額（円）
        data.append(lines[94].replace(",", ""))
        # 外国源泉徴収税額（円）
        data.append(lines[96].replace(",", ""))
        # 国内課税所得額（円）
        data.append(lines[98].replace(",", ""))
        # 所得税（外貨）
        data.append(lines[101].replace(",", ""))
        # 地方税（外貨）
        data.append(lines[104].replace(",", ""))
        # 所得税（円）
        data.append(line103[1].replace(",", ""))
        # 地方税（円）
        data.append(lines[107].replace(",", ""))
        # 国内源泉徴収税額（外貨）
        data.append(lines[106].replace(",", ""))

        return data

    def parse_data_ver2(lines: List[str]) -> List[str]:
        """_summary_

        サンプルデータ(56行の配列データ)
        ```
        0: 2023/03/29
        1: 
        2: 2023/03/30
        3: 
        4: 2023/03/24
        5: 
        6: 304-HDV
        7: 
        8: i | ETF
        9: 
        10: %
        11: 
        12: 1
        13: 
        14: 10.0
        15: 
        16: 1.042139
        17: 
        18: 115
        19: 
        20: 119.85
        21: 
        22: 11.98
        23: 
        24: 0.00
        25: 
        26: 107.87
        27: 
        28: 21.52
        29: 
        30: 0.00
        31: 
        32: 0.00
        33: 
        34: 86.35
        35: 
        36: 2023/03/29
        37: 2023/03/30
        38: 
        39: 130.2800
        40: 132.5500
        41: 
        42: 15,614
        43: 
        44: 1,560
        45: 
        46: 14,054
        47: 
        48: 16.23
        49: 2,152
        50: 
        51: 5.29
        52: 702
        53: 
        54: 21.52
        55: 
        ```

        Args:
            lines (List[str]): _description_

        Returns:
            List[str]: _description_
        """
        assert len(lines) == 56

        data: List[str] = []

        for i, line in enumerate(lines):
            lines[i] = line.strip()

        # 空行をチェック
        for i in list(range(1, 36, 2)) + [38, 41, 43, 45, 47, 50, 53]:
            if lines[i] != "":
                raise ValueError(f"空行チェックエラー: {i}番目の行に空行がありません。 data={repr(lines)}")

        # 配当金等支払日
        data.append(lines[0])
        # 国内支払日
        data.append(lines[2])
        # 現地基準日
        data.append(lines[4])
        # 銘柄コード
        data.append(lines[6])
        # 銘柄名 ※日本語はうまく取得できない。
        data.append(lines[8])
        # 分配通貨 ※うまく取得できないので、固定値を設定
        data.append("※未取得※")
        # 外国源泉税率（%）
        data.append(lines[14])
        # 1単位あたり金額
        data.append(lines[16])
        # 決済方法 ※うまく取得できないので、固定値を設定
        data.append("※未取得※")
        # 数量
        data.append(lines[18].replace(",", ""))
        # 配当金等金額
        data.append(lines[20].replace(",", ""))
        # 外国源泉徴収税額
        data.append(lines[22].replace(",", ""))
        # 外国手数料
        data.append(lines[24].replace(",", ""))
        # 外国精算金額（外貨）
        data.append(lines[26].replace(",", ""))
        # 国内源泉徴収税額（外貨）
        data.append(lines[28].replace(",", ""))
        # 受取金額
        data.append(lines[34].replace(",", ""))
        # 申告レート基準日
        data.append(lines[36])
        # 申告レート
        data.append(lines[39].replace(",", ""))
        # 為替レート基準日
        data.append(lines[37])
        # 為替レート
        data.append(lines[40].replace(",", ""))
        # 配当金等金額（円）
        data.append(lines[42].replace(",", ""))
        # 外国源泉徴収税額（円）
        data.append(lines[44].replace(",", ""))
        # 国内課税所得額（円）
        data.append(lines[46].replace(",", ""))
        # 所得税（外貨）
        data.append(lines[48].replace(",", ""))
        # 地方税（外貨）
        data.append(lines[51].replace(",", ""))
        # 所得税（円）
        data.append(lines[49].replace(",", ""))
        # 地方税（円）
        data.append(lines[52].replace(",", ""))
        # 国内源泉徴収税額（外貨）
        data.append(lines[54].replace(",", ""))

        return data


    lines = text.splitlines()

    next_start_index = 0
    data_length = 56 if pdf_type == PdfType.GLOBAL_STOCK_DIVIDEND_REPORT_VER2 else 112
    while True:
        start_index = search_start_index(lines, next_start_index)

        # 開始位置が見つからない場合は終了
        if start_index == -1:
            break

        if pdf_type == PdfType.GLOBAL_STOCK_DIVIDEND_REPORT_VER1:
            yield parse_data_ver1(lines[start_index:start_index+data_length])
        elif pdf_type == PdfType.GLOBAL_STOCK_DIVIDEND_REPORT_VER2:
            # 対象リストデータを必要に応じて整形
            adjust_lines(lines, start_index)
            # データを抽出
            yield parse_data_ver2(lines[start_index:start_index+data_length])
        else:
            raise NotImplementedError()
        
        # 次の銘柄の開始位置は基本的にはdata_length行後ろだが、少し前から探索する
        next_start_index = start_index + data_length - 5


def list2csv(csv_path: str, data_list: List[str], encoding: str = "cp932") -> None:
    with codecs.open(csv_path, mode="w", encoding=encoding) as f:
        for line in data_list:
            f.write(line)
            f.write("\n")


def read_rdf(file_path: str) -> str:
    txt_file_path = file_path + ".txt"
    if exists(txt_file_path):
        logger.debug(f"テキストファイル読み込み： {txt_file_path}")
        with open(txt_file_path, mode="r", encoding="utf-8") as f:
            return f.read()
    else:
        logger.debug(f"PDFファイル読み込み： {file_path}")
        return extract_text(file_path)

@dataclass
class Arguments:
    input: str | None
    force_save_text: bool


def parse_arguments() -> Arguments:
    parser = argparse.ArgumentParser(description="PDF解析ツール")
    parser.add_argument("-i", "--input", type=str, default=None, help="解析対象のPDFファイルパス。未指定の場合は、対象ディレクトリを再帰的に解析")
    parser.add_argument("-f", "--force-save-text", default=False, action="store_true", help="解析結果を強制的にテキストファイルに保存")
    args = parser.parse_args()

    named_args = {
        "input": args.input,
        "force_save_text": args.force_save_text
    }

    return Arguments(**named_args)


def main(args: Arguments) -> None:
    japanese_stock_dividend_list: List[str] = list()
    global_stock_dividend_list: List[str] = list()

    japanese_stock_dividend_list.append("ファイルパス,銘柄名,銘柄コード,お支払日,配当単価（円）,数量（株数・口数）,配当金額（税引前）（円）,所得税（円）,地方税（円）,端数処理代金（円）,お受取金額（円）")
    global_stock_dividend_list.append(
        "ファイルパス,配当金等支払日,国内支払日,現地基準日,銘柄コード,銘柄名,分配通貨,外国源泉税率（%）,1単位あたり金額,決済方法,数量,配当金等金額,外国源泉徴収税額,外国手数料,外国精算金額（外貨）,国内源泉徴収税額（外貨）,受取金額,申告レート基準日,申告レート,為替レート基準日,為替レート,配当金等金額（円）,外国源泉徴収税額（円）,国内課税所得額（円）,所得税（外貨）,地方税（外貨）,所得税（円）,地方税（円）,国内源泉徴収税額（外貨）")  # noqa E501

    logger.info("処理開始")

    for root, _, files in os.walk(input_dir):
        for file_name in files:
            _, ext = os.path.splitext(file_name)
            file_path = join(root, file_name)

            if file_name.upper().endswith(".PDF.TXT"):
                continue

            # 拡張子がpdfではない場合スキップ
            if not ext.upper().endswith("PDF"):
                logger.debug(f"ファイルスキップ： {file_path}")
                continue

            if args.input and args.input not in file_path:
                logger.debug(f"ファイルスキップ： {file_path}")
                continue

            logger.info(f"解析開始: {file_path}")

            # PDFをテキストに変換。
            # file_path + ".txt"のファイルが存在する場合は、そちらを読み込む。
            # 読み込みに失敗した場合は、file_path + ".txt"にテキストを出力するため、手修正して再度実行する。
            text = read_rdf(file_path)

            save_text = False
            try:
                pdf_type = judge_pdf_type(text)

                logger.debug(f"PDFタイプ： {pdf_type}")
                if pdf_type == PdfType.JAPANESE_STOCK_DIVIDEND_REPORT:
                    for data in parse_japanese_stock_dividend_report(text):
                        data.insert(0, file_path)
                        japanese_stock_dividend_list.append(",".join(data))
                else:
                    for data in parse_global_stock_dividend_report(text, pdf_type):
                        data.insert(0, file_path)
                        global_stock_dividend_list.append(",".join(data))
                
                if args.force_save_text:
                    save_text = True
            except Exception as e:
                logger.error(f"解析エラー: {file_path}")
                save_text = True
                raise e
            finally:
                if save_text and not exists(file_path + ".txt"):
                    with open(file_path + ".txt", mode="w", encoding="utf-8") as f:
                        f.write(text)

            logger.info(f"解析終了: {file_path}")


    logger.info("japanese_stock_dividend.csv 作成開始")
    list2csv(join(output_dir, "japanese_stock_dividend.csv"), japanese_stock_dividend_list)

    logger.info("global_stock_dividend.csv 作成開始")
    list2csv(join(output_dir, "global_stock_dividend.csv"), global_stock_dividend_list)

    logger.info("処理終了")


if __name__ == "__main__":
    formatter = '%(asctime)s [%(levelname)s]: %(message)s'

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(formatter))

    logger.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)
    # logging.basicConfig(level=logger.DEBUG, format=formatter)

    args = parse_arguments()
    main(args)
