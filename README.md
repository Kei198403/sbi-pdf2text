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

## pdf解析ライブラリ

PDFMinerを利用。  
camelot-pyを最初に利用していたが解析に失敗することが増えたり、最新のPythonバージョンに対応していないことから別ライブラリに変更。  
pypdfを試したが日本語が文字化けするため採用は見送った。

```
poetry add pdfminer.six
```

- [pdfminer/pdfminer.six: Community maintained fork of pdfminer - we fathom PDF](https://github.com/pdfminer/pdfminer.six?tab=readme-ov-file)
- [pdfminer Document](https://pdfminersix.readthedocs.io/en/latest/)



## mojimojiライブラリのPython3.12対応

2023年12月時点でmojimoji 0.0.12はpython3.12に未対応。  
2023年10月に[pull request](https://github.com/studio-ousia/mojimoji/pull/25)が出ているが取り込まれていない状況。  
そのためforkされているリポジトリの中からpull requestを取り込んだブランチがあったためそのソースを利用。

```bash
poetry add git+https://github.com/tpdn/mojimoji.git#fix_for_py312
```

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
