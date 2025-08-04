import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio

# .env からトークンなどを読み込む
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "1352701686812246086"))  # 任意のサーバーID

# Botのインテント設定（メッセージやメンバー取得が必要ならここを調整）
intents = discord.Intents.default()

# Botインスタンス作成
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    # スラッシュコマンドをギルド（開発用）に同期
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)

    print(f"✅ ログイン成功: {bot.user}")
    print(f"✅ スラッシュコマンドを {GUILD_ID} に同期完了！")
    print("📋 利用可能コマンド一覧：")
    for cmd in tree.get_commands(guild=guild):
        print(f"🔹 /{cmd.name}")

# Cogファイルを一括ロード
async def load_cogs():
    cog_files = [
        "coins",
        "slot",
        "punching",
        "blackjack",
        "highlow",
        "exchange_title",
        "ranking",
        "loto",
        "give_coin",
        "sin_battle"
    ]
    for cog in cog_files:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ 読み込み成功: {cog}")
        except Exception as e:
            print(f"❌ 読み込み失敗: {cog} - {e}")

# 非同期起動処理
async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

# 実行
if __name__ == "__main__":
    asyncio.run(main())
