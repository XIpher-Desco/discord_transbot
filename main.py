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
IMAGE_CHANNEL_ID = SECRET_DICT['IMAGE_CHANNEL_ID']
IMAGE_FOLDER_ID = SECRET_DICT['IMAGE_DRIVE_ID']
DEEPL_API_KEY = SECRET_DICT['DEEPL_API_KEY']

# channel ファイルの読み込み
CHANNEL_FILE_PATH = './channel_list.yaml'
with open(CHANNEL_FILE_PATH) as f:
    translate_channels = yaml.safe_load(f)

# 絵文字削除(BMP 外と呼ばれるヤツを消す魔法)
NON_BMP_MAP = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '')

# メモ　https://developers.google.com/drive/api/v3/search-files ファイルのサーチワード（フォルダ指定含む）
client = discord.Client()

# deepl の key を予め入れておく
deepl_payload = {'auth_key': DEEPL_API_KEY, 'target_lang': 'JA' }
# r = requests.get("https://api-free.deepl.com/v2/usage", params=payload)

def write_yaml(path, list):
    with codecs.open(path, 'w', 'utf-8') as f:
        yaml.dump(list, f, encoding='utf-8', allow_unicode=True)

def read_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

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

    # json 読み方
    translate_channels = read_yaml(CHANNEL_FILE_PATH)
    if message.content == '/xitraadd':
        translate_channels.append(message.channel.id)
        write_yaml(CHANNEL_FILE_PATH, translate_channels)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を翻訳チャンネルに登録しました")
        return

    if message.content == '/xitradel':
        translate_channels = [i for i in translate_channels if not i == message.channel.id]
        write_yaml(CHANNEL_FILE_PATH, translate_channels)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を翻訳チャンネルから解除しました")
        return

    if message.channel.id in translate_channels:
        # URL 削除
        trancslate_text = re.sub(r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+$,%#]+)", "" ,message.content)

        # 絵文字スタンプ削除
        trancslate_text = re.sub(r"\:[^:]*\:", "" ,trancslate_text)
        trancslate_text = re.sub(r"\<[0-9]+\>", "" ,trancslate_text)
        trancslate_text = trancslate_text.translate(NON_BMP_MAP)

        # 0文字になったら何も返さない
        if len(trancslate_text) == 0:
            return
        deepl_payload['text'] = trancslate_text
        r = requests.get("https://api-free.deepl.com/v2/translate", params=deepl_payload)
        deepl_payload['text'] = ""
        response_message = r.json()['translations'][0]['text']
        if ('JA' != r.json()['translations'][0]['detected_source_language']) :
            await message.channel.send(response_message)
        # await message.channel.send("もうちょっとまってね")

    if message.content == '/xitrausage':
        r = requests.get("https://api-free.deepl.com/v2/usage", params=deepl_payload)
        await message.channel.send(r.text)
        return
        


@client.event
async def my_backgound_task(self):
    """
    backgound task event
    """
    pass

client.run(DISCORD_TOKEN)