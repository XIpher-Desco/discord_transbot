# discord_transbot
個人向け discord 翻訳＋読み上げボット

環境 python3  
discord は discord.py[voice] を使用

## 事前に必要なもの
```
GCP プロジェクト
Discord app
DeepL 開発者アカウント
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
python3 main.py で動く
 
## 機能
```
/xitraadd 翻訳、読み上げチャンネルで実行すると、チャンネルを追加出来る  
/xitradel 翻訳、読み上げチャンネルで実行すると、チャンネルを削除出来る  
/xitrausage deepl のクオータ確認

!xivoijoin 実行者が参加しているボイスチャンネルに参加する。 /xitraadd で事前に追加が必要  
!xivoileave ボイスチャンネルから抜ける  
!xivoiread を頭に付けて、読んでほしい文字入れると読んでくれる。

翻訳
日本語以外だと自動で日本語に翻訳する
/xien を頭につけて発言すると、英語に翻訳する
```
