import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print("古いグローバルスラッシュコマンドを取得中…")
        commands = await self.tree.fetch_commands()
        print(f"削除するコマンド数: {len(commands)}")
        for command in commands:
            print(f"Deleting command: {command.name}")
            await command.delete()  # これで消せるはず
        print("全ての古いグローバルコマンドを削除しました！")
        await self.close()

client = MyClient()
client.run(TOKEN)
