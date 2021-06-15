# discord_transbot
個人向け discord 翻訳＋読み上げボット

環境 python3  
discord は discord.py[voice] を使用

## 事前に必要なもの
```
GCP プロジェクト
 - サービスアカウントと、speech APIとかのライブラリの有効化
Discord app
DeepL 開発者アカウント
 - 無料枠で良い
```

## 追加で必要なファイル それぞれ main.py と同じ場所におく
secret.json  
GCP プロジェクトの サービスアカウントの鍵

secret.yaml  
discord の bot tokenと deepl の api key を書く
```
DISCORD_BOT_TOKEN:
DEEPL_API_KEY: 
```
## 実行
python3 main.py
 
## 機能
```
/xitraadd /xitradel 翻訳 チャンネルの追加削除
/xien を頭につけて発言すると、英語に翻訳します
/xichanstats このチャンネルの登録状況

!xivoiadd, !xivoidel 読み上げチャンネルの追加削除
!xivoialwadd, !xivoialwdel 常時読み上げチャンネルの追加削除
!xivoijoin 実行者が参加しているボイスチャンネルに参加する。 !xivoiadd or !xivoialwaddで事前に追加が必要
!xivoileave ボイスチャンネルからボットを抜く
!xire を頭に付けて、読んでほしい文字入れると読んでくれる（ベータ中）
```
