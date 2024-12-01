## 注意事項
pdfファイルはうまく解析できない場合があります。  
途中でエラーとなったデータについては、解析途中のテキストデータをpdfファイルと同じフォルダ内に拡張子.txtを付与したファイルを出力して、次回そのファイルを読み込むようにしています。  
若干の形式不正の場合は、このテキストファイルを修正して再実行してください。  

## 実行環境
VSCode + Remote Containers + Docker

Python3.12

## Poetryのvirtualenvに入る
VSCodeのTerminalを開くと自動でvirtualenvに入りますが、入らない場合は、以下を実行。

```
source /workspace/.venv/bin/activate
```

参考：https://cocoinit23.com/docker-opencv-importerror-libgl-so-1-cannot-open-shared-object-file/

## workspace内に.venvディレクトリが存在しない場合

以下を実行してください。
```
sh /workspace/.devcontainer/init.sh
```

## 実行
以下のコマンドで実行。
```
python3 sbi-pdf2text.py
```

### データ解析エラーが発生した場合
失敗したpdfファイルと同じ場所に<元のpdfファイル名>.txtというファイルが出力されている。  
エラーログから各行が以下のサンプルデータと同じような表示となるようにテキストファイルの不要行を削除したり、対象行の文字を修正する。  
ただし、「外国株式等　配当金等のご案内」と「株式等配当金のお知らせ」の文字列は削除しないこと。削除するとファイル種別判定でエラーとなる。

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


## pdf解析ライブラリ

PDFMinerを利用。  
camelot-pyを最初に利用していたが解析に失敗することが増えたり、最新のPythonバージョンに対応していないことから別ライブラリに変更。  
pypdfを試したが日本語が文字化けするため採用は見送った。

```
poetry add pdfminer.six
```

- [pdfminer/pdfminer.six: Community maintained fork of pdfminer - we fathom PDF](https://github.com/pdfminer/pdfminer.six?tab=readme-ov-file)
- [pdfminer Document](https://pdfminersix.readthedocs.io/en/latest/)



## GitコミットのPrefixルール

- feat: 新しい機能
- fix: バグの修正
- docs: ドキュメントのみの変更
- style: 空白、フォーマット、セミコロン追加など
- refactor: 仕様に影響がないコード改善(リファクタ)
- perf: パフォーマンス向上関連
- test: テスト関連
- chore: ビルド、補助ツール、ライブラリ関連

## 解析対象

前提：特定口座での受取であること

- 「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ
  - SBI証券
- 「株式等利益剰余金配当金のお知らせ」電子交付のお知らせ
  - SBI証券、SBIネオモバイル証券
