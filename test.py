import discord
from discord.commands import Option
import json
import yaml
import requests
import codecs
import sys 
import secret #標準のjsonモジュールとconfig.pyの読み込み


### 定数設定
# ================
DISCORD_TOKEN = secret.DISCORD_BOT_TOKEN
DEEPL_API_KEY = secret.DEEPL_API_KEY
ADMIN_IDS = secret.ADMIN_IDS

CHANNEL_FILE_PATH = './channel_list.yaml'
NON_BMP_MAP = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '')

VOICE_FILE_PATH = './voice.mp3'

class channel_schema:
    # yaml の構造呼び出しに使う（文字列から変数に入れておきたい）
    TRANSLATE = 'translate'
    VOICE = 'voice'
    ACTIVE = 'active'
    ALWAYS = 'always'

### 便利な関数
# ================

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

# def set_channel_config(channel_id, channel_type, active_always, is_active: bool):
#     """
#     チャンネルの設定を変更して、リストをファイルに書き込む関数
#     schema 定義が雑ですまんな。 TRANSLATE は ALWAYS は今の所無い
#     channel_type: channel_schema.TRANSLATE, channel_schema.VOICE
#     active_always: channel_schema.ACTIVE, channel_schema.ALWAYS
#     is_active: 指定のものをどうするか
#     """
#     registered_channel_list = read_yaml(CHANNEL_FILE_PATH)
#     target_channel = get_channel_config(registered_channel_list, channel_id)
#     target_channel[channel_type][active_always] = is_active
#     registered_channel_list[channel_id] = target_channel
#     write_yaml(CHANNEL_FILE_PATH, registered_channel_list)
#     return registered_channel_list


bot = discord.Bot()
# ctx = discord.py の context とほぼ同じ
# https://discordpy.readthedocs.io/ja/latest/ext/commands/api.html#context
@bot.slash_command(guild_ids=[281115820455624704])
async def xi(ctx):
    await ctx.respond('pong')
    
@bot.slash_command(guild_ids=[281115820455624704])
async def ping(ctx):
    await ctx.respond('pong')

@bot.slash_command(guild_ids=[281115820455624704], description="挨拶を返すよ")
async def xihello(ctx, name: str = None):
    """Say hello to the bot"""
    name = name or ctx.author.nick
    await ctx.respond(f"Hello {name}!")
    print(ctx.message)
    print(ctx.channel)
    print(ctx.author)
    print(ctx.author.voice.channel)

@bot.slash_command(guild_ids=[281115820455624704], description="読み上げを起動するよ")
async def xiconnect(ctx, name: str = None):
    name = name or ctx.author.name
    if ctx.author.voice is None:
        await ctx.respond("あなたはボイスチャンネルに接続してないみたいだよ＞＿＜；")
        return
    await ctx.author.voice.channel.connect()
    await ctx.respond("接続したよ！")

@bot.slash_command(guild_ids=[281115820455624704], description="読み上げを終了するよ")
async def xidisconnect(ctx, name: str = None):
    # 切断する
    await ctx.guild.voice_client.disconnect()
    await ctx.respond("切断したよ、また呼んでね。")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_voice_state_update(member, before, after):
    # if not(before.channel.guild.voice_client is None):
    #     if after.channel is None:
    #         before.channel.guild.voice_client.disconnect()
    # 該当チャンネルに接続してるか確認
    # if not(after.channel.guild.voice_client is None):
    #     # bot 以外のメンバーリスト作成
    #     non_bot_members = [
    #         mem for mem in after.channel.members if mem.bot == False]
    #     # メンバーが０人なら、切断
    #     if len(non_bot_members) == 0:
    #         after.channel.guild.voice_client.disconnect()

    """
    voice channel から ボット以外いなくなったら切断する
    """
    # before, after でボイスチャンネルの移動前と移動先がわかるらしい
    # before とは言ってるが、移動後（つまり抜けたあと）のチャンネルの状態。誰も居なくなったら member は 0 人になる
    if before.channel != after.channel:
        # before.channelとafter.channelが異なるなら入退室
        if after.channel:
            # もし、ボイスチャットが開始されたら
            pass

        if before.channel:
            # もし、ボイスチャットが終了したら
            if not(before.channel.guild.voice_client is None):
                # 繋がっていれば
                non_bot_members = [
                    mem for mem in before.channel.members if mem.bot == False]
                if len(non_bot_members) == 0:
                    await before.channel.guild.voice_client.disconnect()

bot.run(DISCORD_TOKEN)