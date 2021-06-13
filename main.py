"""This is a test program."""
# import datetime
import asyncio
from logging import fatal
import os
from time import sleep
# import time
# import io
import discord
import yaml
import requests
import codecs
import re
import sys
import random
# from apiclient import discovery
# from google.cloud import translate
from google.cloud import texttospeech
# from google.oauth2.service_account import Credentials
# from googleapiclient.http import MediaIoBaseDownload

# credential_file_path = "./secret.json"
# # service account クレデンシャル読み込み
# c = Credentials.from_service_account_file(
#     credential_file_path, scopes=["https://www.googleapis.com/auth/drive"]
# )

# drive_service = discovery.build('drive', 'v3', credentials=c)

# 定数設定
SECRET_PATH = './secret.yaml'
with open(SECRET_PATH) as f:
    SECRET_DICT = yaml.safe_load(f)

DISCORD_TOKEN = SECRET_DICT['DISCORD_BOT_TOKEN']
DEEPL_API_KEY = SECRET_DICT['DEEPL_API_KEY']
ADMIN_IDS = []
if 'ADMIN_IDS' in SECRET_DICT:
    ADMIN_IDS = SECRET_DICT['ADMIN_IDS']

# 翻訳システムの 事前実行 ここから-------
CHANNEL_FILE_PATH = './channel_list.yaml'


# 絵文字削除(BMP 外と呼ばれるヤツを消す魔法)
NON_BMP_MAP = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '')

VOICE_FILE_PATH = './voice.mp3'


class channel_schema:
    # yaml の構造呼び出しに使う（文字列から変数に入れておきたい）
    TRANSLATE = 'translate'
    VOICE = 'voice'
    ACTIVE = 'active'
    ALWAYS = 'always'


# deepl の key を予め入れておく
deepl_payload = {'auth_key': DEEPL_API_KEY, 'target_lang': 'JA'}
# 翻訳システムの 事前実行 ここまで-------

# google texttospeech のクライアント作成
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


def get_channel_config(channel_list, channel_id):
    """
    チャンネルリストから channel_id 指定して取得する。
    なんで面倒臭いことしているかと言えば、スキーマを定義したいから一々変数存在チェックしたくない...
    """
    if channel_id in channel_list:
        return channel_list[channel_id]
    else:
        return {'voice': {'active': False,
                          'always': False}, 'translation': {'active': False}}


def set_channel_config(channel_id, channel_type, active_always, is_active: bool):
    """
    schema 定義が雑ですまんな。 TRANSLATE は ALWAYS は今の所無い
    channel_type: channel_schema.TRANSLATE, channel_schema.VOICE
    active_always: channel_schema.ACTIVE, channel_schema.ALWAYS
    is_active: 指定のものをどうするか
    """
    registered_channel_list = read_yaml(CHANNEL_FILE_PATH)
    target_channel = get_channel_config(registered_channel_list, channel_id)
    target_channel[channel_type][active_always] = is_active
    registered_channel_list[channel_id] = target_channel
    write_yaml(CHANNEL_FILE_PATH, registered_channel_list)
    return registered_channel_list


def get_voice(read_text, file_path):
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
    with open(file_path, "wb") as out:
        out.write(response.audio_content)

        # print('Audio content written to file "./voice.mp3"')
        # 読み上げ


def play_voice(voice_channnel, voice_path, e):
    """
    読み上げに失敗したら、待機する・・・多分
    """
    print(voice_path, e)
    if e == None:
        os.remove(voice_path)
        print("delete " + voice_path)
        return
    sleep(0.1)
    print("失敗")
    voice_channnel.play(discord.FFmpegPCMAudio(
        voice_path), after=lambda e: play_voice(voice_channnel, voice_path, e))

    # while True:
    #     await event.wait()
    #     event.clear()
    #     if e == None:
    #         os.remove(voice_path)
    #         print("delete " + voice_path)
    #         return
    #     voice_channnel.play(discord.FFmpegPCMAudio(
    #         voice_path, after=lambda e: event.set()))
    #     os.remove(voice_path)


voices = asyncio.Queue()
play_next_voice = asyncio.Event()


async def play_voice_task():
    while True:
        play_next_voice.clear()
        current = await voices.get()
        current.start()
        print("aaaaaa")
        await play_next_voice.wait()

# 起動時に動作する処理
# 翻訳 channel ファイルの読み込み
registered_channels = read_yaml(CHANNEL_FILE_PATH)


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
    # ヘルプ
    if re.match(r"[!/]xihelp", message.content):
        help_messages = ""
        if message.author.id in ADMIN_IDS:
            help_messages = r"""```
翻訳系:
/xitraadd, /xitradel, /xien, /xichanstats
読み上げ系:
!xivoiadd, !xivoidel, !xivoialwadd, !xivoialwdel
!xivoijoin, !xivoileave, !xire
```"""
        else:
            help_messages = r"""```
/xitraadd /xitradel 翻訳 チャンネルの追加削除
/xien を頭につけて発言すると、英語に翻訳します
/xichanstats このチャンネルの登録状況

!xivoiadd, !xivoidel 読み上げチャンネルの追加削除
!xivoialwadd, !xivoialwdel 常時読み上げチャンネルの追加削除
!xivoijoin 実行者が参加しているボイスチャンネルに参加する。 !xivoiadd or !xivoialwaddで事前に追加が必要
!xivoileave ボイスチャンネルからボットを抜く
!xire を頭に付けて、読んでほしい文字入れると読んでくれる（ベータ中）
```"""
        await message.channel.send(help_messages)
        return
    # 翻訳チャンネル追加と削除
    global registered_channels
    if message.content == '/xitraadd':
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.TRANSLATE, channel_schema.ACTIVE, True)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を翻訳チャンネルに登録しました")
        return

    elif message.content == '/xitradel':
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.TRANSLATE, channel_schema.ACTIVE, False)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を翻訳チャンネルから解除しました")
        return
    # 読み上げチャンネル追加と削除
    elif message.content == '!xivoiadd':
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.VOICE, channel_schema.ACTIVE, True)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を読み上げチャンネルに登録しました")
        return

    elif message.content == '!xivoidel':
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.VOICE, channel_schema.ACTIVE, False)
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.VOICE, channel_schema.ALWAYS, False)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を読み上げチャンネルから解除しました")
        return
    elif message.content == '!xivoialwadd':
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.VOICE, channel_schema.ACTIVE, True)
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.VOICE, channel_schema.ALWAYS, True)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を常時読み上げチャンネルに登録しました")
        return

    elif message.content == '!xivoialwdel':
        registered_channels = set_channel_config(
            message.channel.id, channel_schema.VOICE, channel_schema.ALWAYS, False)
        await message.channel.send('チャンネル: ' + str(message.channel.name) + " を常時読み上げチャンネルから解除しました")
        return
    # 翻訳上限確認 事前に secret.yaml に ADMIN_IDSの記載が必要
    elif message.content == '/xitrausage':
        if message.author.id in ADMIN_IDS:
            r = requests.get("https://api-free.deepl.com/v2/usage",
                             params=deepl_payload)
            await message.channel.send(r.text)
        return
    # チャンネルのステータス確認
    elif message.content == '/xichanstats':
        await message.channel.send(yaml.dump(get_channel_config(registered_channels, message.channel.id)))

    # 以下登録チャンネルでのみ動作する機能 登録チャンネル以外はここでブレイクするように
    if message.channel.id not in registered_channels:
        return
    # 発言チャンネルの設定を取得
    channel_config = get_channel_config(
        registered_channels, message.channel.id)

    """
    メモ
    翻訳がアクティブ -> 基本日本語以外を翻訳して bot が発言
    翻訳 + 読み上げがアクティブ -> 日本語判定されたらそのまま読み上げ、要翻訳判定されたら翻訳したやつを読む
    連携に関して考え中
    """
    # テキストチェック、キレイ化＋フラグ処理
    xi_command_list = [r"/xien", r"!xire"]
    xi_command_regular = '|'.join(xi_command_list)

    # 翻訳フラグ
    translate_flag = channel_config[channel_schema.TRANSLATE][channel_schema.ACTIVE]
    # 日->英フラグ
    ja_to_en = False
    # 読み上げフラグ
    read_aloud_flag = channel_config[channel_schema.VOICE][channel_schema.ACTIVE]

    # 指定コマンド以外が入力されていたら、全フラグをfalseに
    # 特定文字列(あるbotの予備出しコマンド)も全フラグ false に
    if re.match(xi_command_regular, message.content):
        pass
    elif re.match(r"[!/]", message.content):
        translate_flag = False
        read_aloud_flag = False
    elif re.match(r"^[ｍm]$", message.content):
        translate_flag = False
        read_aloud_flag = False

    # 翻訳系フラグ
    # 日本語 -> 英語コマンドの判定
    if translate_flag:
        if re.match(r"/xien", message.content):
            ja_to_en = True

    # 読み上げ系フラグ
    if read_aloud_flag:
        # コマンドがついてる or 常時読み上げが有効ならそのまま（True）でなければ False
        if message.guild.voice_client is None:
            read_aloud_flag = False
        if re.match(r'!xire', message.content):
            if message.guild.voice_client is None:
                await message.channel.send("ボイスチャンネルに接続していないため、再生出来ません")
        elif channel_config[channel_schema.VOICE][channel_schema.ALWAYS]:
            pass
        else:
            read_aloud_flag = False

    # コマンド列消した文字を入れておく 以降 message.content は使わない
    cleanup_translate_text = re.sub(
        xi_command_regular, "", message.content)
    cleanup_read_aloud_text = re.sub(
        xi_command_regular, "", message.content)
    # 翻訳または読み上げが有効なら、文字をキレイにする (URL 差分)
    if translate_flag:
        cleanup_translate_text = cleanupTexts(cleanup_translate_text)
    if read_aloud_flag:
        cleanup_read_aloud_text = cleanupTexts(
            cleanup_read_aloud_text, URL_REMOVE=False)

    # 0文字になったらフラグを false
    if len(cleanup_translate_text) == 0:
        translate_flag = False
    if len(cleanup_read_aloud_text) == 0:
        read_aloud_flag = False

    # 日英翻訳ON or 単語が日本語じゃなければ翻訳有効
    if (not(ja_to_en) and is_japanese(cleanup_translate_text)):
        translate_flag = False
# 以降まだ未調整
# 翻訳系
    if translate_flag:
        deepl_payload['text'] = cleanup_translate_text

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
        translated_text = r.json()['translations'][0]['text']

        # 日本語翻訳機能ON または、日本語以外なら翻訳文を投げる
        if (ja_to_en or ('JA' != r.json()['translations'][0]['detected_source_language'])):
            await message.channel.send(translated_text)

    # 読み上げ チャンネルログイン周りコマンド
    if channel_config[channel_schema.VOICE][channel_schema.ACTIVE]:
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

    # 読み上げフラグ
    if read_aloud_flag:
        read_text = cleanup_read_aloud_text
        # 文字数制限 47 文字
        read_text = re.sub(r"(.{47}).*", r"\1以下略", read_text)
        # 先頭に発言者つける、 nick だと 登録してない人が使ったらバグって即死する要修正
        if type(message.author.nick) is str:
            read_text = message.author.nick + "さん、" + read_text
        elif type(message.author.name) is str:
            read_text = message.author.name + "さん、" + read_text
        mp3_file_path = "./voice_" + \
            str(random.randint(0, 100000)).zfill(6) + ".mp3"
        get_voice(read_text, mp3_file_path)
        # voices.put(message.guild.voice_client.play(discord.FFmpegOpusAudio(
        #     mp3_file_path), after=lambda e: play_voice(message.guild.voice_client, mp3_file_path, e)))
        while True:
            if not(message.guild.voice_client.is_playing()):
                break
        message.guild.voice_client.play(discord.FFmpegOpusAudio(
            mp3_file_path), after=lambda e: play_voice(message.guild.voice_client, mp3_file_path, e))
        # mp3_file_path), after=lambda e: (await play_voice(message.guild.voice_client, mp3_file_path, e) for _ in '_').__anext__())
        # os.remove(mp3_file_path)

        if translate_flag:
            read_text = translated_text
            # 文字数制限 47 文字
            read_text = re.sub(r"(.{47}).*", r"\1以下略", read_text)
            read_text = "翻訳、" + read_text
            mp3_file_path = "./voice_" + \
                str(random.randint(0, 100000)).zfill(6) + ".mp3"
            get_voice(read_text, mp3_file_path)
            sleep(0.1)  # 発言者の読み上げを先にする... Todo なんとかしたい
            # voices.put(message.guild.voice_client.play(discord.FFmpegOpusAudio(
            #     mp3_file_path), after=lambda e: play_voice(message.guild.voice_client, mp3_file_path, e)))
            while True:
                if not(message.guild.voice_client.is_playing()):
                    break
            message.guild.voice_client.play(discord.FFmpegOpusAudio(
                mp3_file_path), after=lambda e: play_voice(message.guild.voice_client, mp3_file_path, e))
            # mp3_file_path), after=lambda e: (await play_voice(message.guild.voice_client, mp3_file_path, e) for _ in '_').__anext__())
        #     os.remove(mp3_file_path)


@ client.event
async def my_backgound_task(self):
    """
    backgound task event
    """
    pass
# client.loop.create_task(play_voice_task())
client.run(DISCORD_TOKEN)
