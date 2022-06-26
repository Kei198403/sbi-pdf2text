## 注意事項
『「外国株式等配当金等のご案内（兼）支払通知書」電子交付のお知らせ』はうまく解析できない場合があります。

## 実行環境
VSCode + Remote Containers + Docker

Python3.9

※2022年4月時点でPython3.10ではcamelotのインストールができませんでした。

## Poetryのvirtualenvに入る
VSCodeのTerminalを開くと自動でvirtualenvに入りますが、入らない場合は、以下を実行。

```
source /workspace/.venv/bin/activate
```

参考：https://cocoinit23.com/docker-opencv-importerror-libgl-so-1-cannot-open-shared-object-file/

## pdf解析パッケージ

```
poetry add "camelot-py[base]"
```

- [Camelot: PDF Table Extraction for Humans](https://camelot-py.readthedocs.io/en/master/)
- [Pythonを使えばテキストを含むPDFの解析は簡単だ・・・そんなふうに考えていた時期が俺にもありました](https://qiita.com/mima_ita/items/d99afc28b6f51479f850)

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
