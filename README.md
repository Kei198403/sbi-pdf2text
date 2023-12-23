## 注意事項
『「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ』はうまく解析できない場合があります。

## 実行環境
VSCode + Remote Containers + Docker

Python3.12

## Poetryのvirtualenvに入る
VSCodeのTerminalを開くと自動でvirtualenvに入りますが、入らない場合は、以下を実行。

```
source /workspace/.venv/bin/activate
```

参考：https://cocoinit23.com/docker-opencv-importerror-libgl-so-1-cannot-open-shared-object-file/

## pdf解析パッケージ

```
poetry add pypdf"
```

- [pypdf · PyPI](https://pypi.org/project/pypdf/)
- [【Python×PDF】PyPDF2はもう古い！PythonでPDFを扱うときにはpypdfを使おう #Python - Qiita](https://qiita.com/ryutarom128/items/6e5d36efb136f9595f07)

## mojimojiライブラリのPython3.12対応

2023年12月時点でmojimoji 0.0.12はpython3.12に未対応。  
[pull request](https://github.com/studio-ousia/mojimoji/pull/25)が出ているが取り込まれていない状況だった。  
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
