# 拡張機能
- （必須）Remote Development
- （任意）Git History

# 流れ
- devcontainer.jsonを読み込む
- Docker環境構築
- Remote Development拡張機能を介してVSCodeがコンテナに接続
- .vscodeフォルダに格納されたデバッグ構成ファイル「launch.json」を読み込んで、デバッグの構成を行う。

# devcontainer.json
Dockerコンテナの設定を記載する。  
あとは、VSCodeのエディタ設定もここに記載。  

# プロジェクト毎の基本設定
.vscodeディレクトリのsettings.jsonで定義できる

# dockerのビルドキャッシュをクリアする方法

```
# キャッシュサイズ確認
docker system df
# キャッシュをクリア（コンテナ削除後に実行すること）
docker builder prune
```
