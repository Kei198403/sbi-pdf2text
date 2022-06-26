#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import camelot
import re
import codecs

from os.path import join
from typing import Final, List, cast, Generator

from camelot.core import TableList, Table
from pandas import DataFrame
from enum import Enum
from mojimoji import zen_to_han

input_dir: Final[str] = "./input"
output_dir: Final[str] = "./output"

re_date_format = re.compile(r"\d{4}/\d{2}/\d{2}")


class PdfType(Enum):
    # 「株式等利益剰余金配当金のお知らせ」電子交付のお知らせ
    JAPANESE_STOCK_DIVIDEND_REPORT = 1
    # 「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ
    GLOBAL_STOCK_DIVIDEND_REPORT = 2


def judge_pdf_type(table: Table) -> PdfType:
    df = cast(DataFrame, table.df)

    if re_date_format.match(cast(str, df.loc[1][0]).strip()):
        return PdfType.GLOBAL_STOCK_DIVIDEND_REPORT

    for i in df.index:
        if "特定口座配当等受入対象" in df.loc[i][2]:
            return PdfType.JAPANESE_STOCK_DIVIDEND_REPORT

    raise NotImplementedError()


def parse_japanese_stock_dividend_report(tables: TableList) -> Generator[List[str], None, None]:
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
        tables (TableList): camelot.read_pdfの返却値
    """
    for i in range(tables.n):
        table: Table = tables[i]
        df = cast(DataFrame, table.df)

        if len(df.columns) < 10:
            continue

        base_position = (3, 8)
        for pos in base_position:
            # 「以下余白」が含まれている場合はスキップ
            if "以下余白" in df.loc[pos][0]:
                continue

            # 改行区切りになっている銘柄名と銘柄コードを分割
            corporation = cast(str, df.loc[pos][0]).split("\n")

            data = list()
            # 銘柄名
            data.append(corporation[0].strip())
            # 銘柄コード
            data.append(zen_to_han(corporation[1].strip().replace("　", "").replace("（", "").replace("）", "")))
            # お支払日
            data.append(zen_to_han(df.loc[pos][4].replace("　", "")))
            # 配当単価（円）
            data.append(zen_to_han(df.loc[pos][8]))
            # 数量（株数・口数）
            data.append(zen_to_han(df.loc[pos][12].replace("，", "")))
            # 配当金額（税引前）
            data.append(zen_to_han(df.loc[pos+2][0].replace("，", "")))
            # 所得税（円）
            data.append(zen_to_han(df.loc[pos+2][2].replace("，", "")))
            # 地方税（円）
            data.append(zen_to_han(df.loc[pos+2][3].replace("，", "")))
            # 端数処理代金（円）
            data.append(zen_to_han(df.loc[pos+2][8].replace("，", "")))
            # お受取金額（円）
            data.append(zen_to_han(df.loc[pos+2][12].replace("，", "")))

            yield data


def parse_global_stock_dividend_report(tables: TableList) -> Generator[List[str], None, None]:
    """『「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ』PDFを解析して、情報を抽出。

    pdfの構成：
      1銘柄に対して、tableが2つ。

    tables[n+0].df
      縦：0～6、横：0～14のDataFrameオブジェクト
    tables[n+1].df
      縦：0～3、横：0～8のDataFrameオブジェクト

    Args:
        tables (TableList): _description_
    """
    for i in range(tables.n//2):
        table1: Table = tables[i*2 + 0]
        table2: Table = tables[i*2 + 1]
        df1 = cast(DataFrame, table1.df)
        df2 = cast(DataFrame, table2.df)

        data: List[str] = list()

        # 配当金等支払日
        data.append(df1.loc[1][0])
        # 国内支払日
        data.append(df1.loc[1][1])
        # 現地基準日
        data.append(df1.loc[1][2])
        # 銘柄コード
        data.append(df1.loc[1][4])
        # 銘柄名
        data.append(df1.loc[1][7])
        # 分配通貨
        data.append(df1.loc[3][0])
        # 外国源泉税率（%）
        data.append(df1.loc[3][1])
        # 1単位あたり金額
        data.append(df1.loc[3][2])
        # 決済方法
        data.append(df1.loc[3][4])
        # 数量
        data.append(df1.loc[5][0])
        # 配当金等金額
        data.append(df1.loc[5][1])
        # 外国源泉徴収税額
        data.append(df1.loc[5][2])
        # 外国手数料
        data.append(df1.loc[6][3])
        # 外国精算金額（外貨）
        data.append(df1.loc[5][5])
        # 国内源泉徴収税額（外貨）
        data.append(df1.loc[5][8])
        # 受取金額
        data.append(df1.loc[5][12])
        # 申告レート基準日
        data.append(df2.loc[2][0])
        # 申告レート
        data.append(df2.loc[2][1])
        # 為替レート基準日
        data.append(df2.loc[3][0])
        # 為替レート
        data.append(df2.loc[3][1])
        # 配当金等金額（円）
        data.append(df2.loc[2][2].replace(",", ""))
        # 外国源泉徴収税額（円）
        data.append(df2.loc[2][3].replace(",", ""))
        # 国内課税所得額（円）
        data.append(df2.loc[2][4].replace(",", ""))
        # 所得税（外貨）
        data.append(df2.loc[2][5])
        # 地方税（外貨）
        data.append(df2.loc[2][7])
        # 所得税（円）
        data.append(df2.loc[3][6].replace(",", ""))
        # 地方税（円）
        data.append(df2.loc[3][7].replace(",", ""))
        # 国内源泉徴収税額（外貨）
        data.append(df2.loc[2][8])

        yield data


def main() -> None:
    japanese_stock_dividend_list: List[str] = list()
    global_stock_dividend_list: List[str] = list()

    japanese_stock_dividend_list.append("ファイルパス,銘柄名,銘柄コード,お支払日,配当単価（円）,数量（株数・口数）,配当金額（税引前）（円）,所得税（円）,地方税（円）,端数処理代金（円）,お受取金額（円）")
    global_stock_dividend_list.append(
        "ファイルパス,配当金等支払日,国内支払日,現地基準日,銘柄コード,銘柄名,分配通貨,外国源泉税率（%）,1単位あたり金額,決済方法,数量,配当金等金額,外国源泉徴収税額,外国手数料,外国精算金額（外貨）,国内源泉徴収税額（外貨）,受取金額,申告レート基準日,申告レート,為替レート基準日,為替レート,配当金等金額（円）,外国源泉徴収税額（円）,国内課税所得額（円）,所得税（外貨）,地方税（外貨）,所得税（円）,地方税（円）,国内源泉徴収税額（外貨）")  # noqa E501

    for root, _, files in os.walk(input_dir):
        for file_name in files:
            file_path = join(root, file_name)
            print(file_path)

            tables: TableList = camelot.read_pdf(
                file_path, pages="all", line_scale=60,
                layout_kwargs={'char_margin': 0.2, 'line_margin': 0.5, 'line_overlap': 0.5, 'word_margin': 0.1}
            )

            pdf_type = judge_pdf_type(cast(Table, tables[0]))
            if pdf_type == PdfType.JAPANESE_STOCK_DIVIDEND_REPORT:
                for data in parse_japanese_stock_dividend_report(tables):
                    data.insert(0, file_path)
                    japanese_stock_dividend_list.append(",".join(data))
            else:
                for data in parse_global_stock_dividend_report(tables):
                    data.insert(0, file_path)
                    global_stock_dividend_list.append(",".join(data))

    with codecs.open(join(output_dir, "japanese_stock_dividend.csv"), mode="w", encoding="cp932") as f:
        for line in japanese_stock_dividend_list:
            f.write(line)
            f.write("\n")

    with codecs.open(join(output_dir, "global_stock_dividend.csv"), mode="w", encoding="cp932") as f:
        for line in global_stock_dividend_list:
            f.write(line)
            f.write("\n")


if __name__ == "__main__":
    main()
