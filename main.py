"""This is a test program."""
import datetime
import time
import io
import discord
import yaml
import requests
import codecs
import re
import sys
from apiclient import discovery
from google.cloud import translate
from google.cloud import texttospeech
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload

# credential_file_path = "./secret.json"
# # service account クレデンシャル読み込み
# c = Credentials.from_service_account_file(
#     credential_file_path, scopes=["https://www.googleapis.com/auth/drive"]
# )

# drive_service = discovery.build('drive', 'v3', credentials=c)

# 定数読み込み
SECRET_PATH = './secret.yaml'
with open(SECRET_PATH) as f:
    SECRET_DICT = yaml.safe_load(f)

DISCORD_TOKEN = SECRET_DICT['DISCORD_BOT_TOKEN']
DEEPL_API_KEY = SECRET_DICT['DEEPL_API_KEY']

# 翻訳システムの 事前実行 ここから-------
# 翻訳 channel ファイルの読み込み
CHANNEL_FILE_PATH = './channel_list.yaml'
with open(CHANNEL_FILE_PATH) as f:
    translate_channels = yaml.safe_load(f)

# 絵文字削除(BMP 外と呼ばれるヤツを消す魔法)
NON_BMP_MAP = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '')

# deepl の key を予め入れておく
deepl_payload = {'auth_key': DEEPL_API_KEY, 'target_lang': 'JA'}
# 翻訳システムの 事前実行 ここまで-------

texttospeech_client = texttospeech.TextToSpeechClient()


# ディスコードクライアント生成
client = discord.Client()

# 便利関数（外だししたいけど）


def write_yaml(path, list):
    """
    yaml file write
    """
    with codecs.open(path, 'w', 'utf-8') as f:
        yaml.dump(list, f, encoding='utf-8', allow_unicode=True)


def read_yaml(path):
    """
    yaml file read
    """
    with open(path) as f:
        return yaml.safe_load(f)

# 文字列クリーンアップ


def cleanupTexts(text, URL_REMOVE=True):
    """
    翻訳や読み上げに不要な文字を削除するよ
    例えば URL を消すか "URL" という文字列にするよ。
    あとは :aaaa: や🔥とかいうゴミ消すよ。
    discord の絵文字 <a0000> <0000> も消すよ。
    """
    if URL_REMOVE:
        text = re.sub(
            r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "", text)
    else:
        text = re.sub(
            r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "URL", text)
    # 絵文字スタンプ削除
    text = re.sub(r"\:[^:]*\:", "", text)
    text = re.sub(r"\<a*[0-9]+\>", "", text)
    text = text.translate(NON_BMP_MAP)
    return text


def is_japanese(str):
    """
    ひらがな、カタカナがあれば多分日本語　精度悪ければ外す。
    """
    return True if re.search(r'[ぁ-んァ-ン]', str) else False

# 起動時に動作する処理


@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    # deepl の制限表示
    # payload = {'auth_key': DEEPL_API_KEY}
    # r = requests.get("https://api-free.deepl.com/v2/usage", params=deepl_payload)
    # print(r.json())


@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return

    # ! or / コマンドは上の方で対応
    # 翻訳チャンネル追加と削除
    translate_channels = read_yaml(CHANNEL_FILE_PATH)
    if message.content == '/xitraadd':
        translate_channels.append(message.channel.id)
        write_yaml(CHANNEL_FILE_PATH, translate_channels)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を翻訳+読み上げチャンネルに登録しました")
        return

    elif message.content == '/xitradel':
        translate_channels = [
            i for i in translate_channels if not i == message.channel.id]
        write_yaml(CHANNEL_FILE_PATH, translate_channels)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を翻訳+読み上げチャンネルから解除しました")
        return

    # 翻訳上限確認
    elif message.content == '/xitrausage':
        r = requests.get("https://api-free.deepl.com/v2/usage",
                         params=deepl_payload)
        await message.channel.send(r.text)
        return

    # 以下登録チャンネルでのみ動作する機能 登録チャンネル以外はここでブレイクするように
    if message.channel.id not in translate_channels:
        return

    # voice channel ログインログアウト
    if message.content == "!xivoijoin":
        if message.author.voice is None:
            await message.channel.send("あなたはボイスチャンネルに接続していません。 読み上げ機能を有効にするには、ボイスチャンネルに参加してください。")
            return
        # ボイスチャンネルに接続する
        await message.author.voice.channel.connect()
        await message.channel.send("接続しました。")

    elif message.content == "!xivoileave":
        if message.guild.voice_client is None:
            await message.channel.send("私はボイスチャンネルに接続していません。")
            return

        # 切断する
        await message.guild.voice_client.disconnect()

        await message.channel.send("切断しました。")

    if re.match(r"!xivoiread", message.content):
        if message.guild.voice_client is None:
            await message.channel.send("ボイスチャンネルに接続していないため、再生出来ません")
            return

        # コマンド部分削除
        read_text = re.sub(r"!xivoiread", "", message.content)
        read_text = cleanupTexts(read_text, URL_REMOVE=False)
        # 文字数制限 47 文字
        read_text = re.sub(r"(.{47}).*", r"\1以下略", read_text)

        read_text = message.author.nick + "さん、" + read_text
        synthesis_input = texttospeech.SynthesisInput(
            text=read_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name="ja-JP-Wavenet-B",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
            pitch=3.0
        )

        response = texttospeech_client.synthesize_speech(
            request={"input": synthesis_input,
                     "voice": voice, "audio_config": audio_config}
        )

        # The response's audio_content is binary.
        with open("voice.mp3", "wb") as out:
            out.write(response.audio_content)
            # print('Audio content written to file "voice.mp3"')
        # 読み上げ

        message.guild.voice_client.play(discord.FFmpegOpusAudio("voice.mp3"))

    # 翻訳
    trancslate_ecommand_list = ["/xien"]
    trancslate_text = message.content
    ja_to_en = False
    # 一部特定文字の場合即時リターン (先頭! とか / のやつ)
    if "m" == trancslate_text:
        return
    elif re.match(r"/xien", trancslate_text):
        # 日本語 -> 英語コマンドの判定
        ja_to_en = True
    elif re.match(r"[!/]", trancslate_text):
        return

    # /xien のコマンドを消すように
    trancslate_text = re.sub(r"/xien", "", trancslate_text)
    trancslate_text = cleanupTexts(trancslate_text)
    # 0文字になったら何も返さない
    if len(trancslate_text) == 0:
        return
    # 日英翻訳ON or 単語が日本語じゃなければ DeepL に行く
    if (ja_to_en or not(is_japanese(trancslate_text))):
        deepl_payload['text'] = trancslate_text

        # 日英コマンドが ON ならターゲットを英にする
        if (ja_to_en):
            deepl_payload['target_lang'] = 'EN-US'
        # 翻訳リクエスト
        r = requests.get(
            "https://api-free.deepl.com/v2/translate", params=deepl_payload)

        # ローカルコピーだから戻さなくても大丈夫だと思うけど...
        deepl_payload['text'] = ""
        deepl_payload['target_lang'] = 'JA'

        # レスポンスメッセージ（翻訳後）を取得
        response_message = r.json()['translations'][0]['text']

        # 日本語翻訳機能ON または、日本語以外なら翻訳文を投げる
        if (ja_to_en or ('JA' != r.json()['translations'][0]['detected_source_language'])):
            await message.channel.send(response_message)
        # await message.channel.send("もうちょっとまってね")


@ client.event
async def my_backgound_task(self):
    """
    backgound task event
    """
    pass

client.run(DISCORD_TOKEN)
