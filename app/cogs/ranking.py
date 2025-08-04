import discord
from discord.ext import commands
from discord import app_commands
import json
import os

GUILD_ID = 1352701686812246086
COIN_FILE = "coins.json"

def load_data():
    if not os.path.exists(COIN_FILE):
        with open(COIN_FILE, "w") as f:
            json.dump({}, f)
    with open(COIN_FILE, "r") as f:
        return json.load(f)

class RankingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="c_ranking", description="所持コインランキング")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def coin_ranking(self, interaction: discord.Interaction):
        data = load_data()
        sorted_data = sorted(data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)

        lines = []
        for i, (user_id, user_data) in enumerate(sorted_data, start=1):
            user = await self.bot.fetch_user(int(user_id))
            coins = user_data.get("coins", 0)
            lines.append(f"{i}. {user.name} - {coins}枚")

        msg = "\n".join(lines) if lines else "ランキングデータがありません。"
        await interaction.response.send_message(f"🏆 **所持コインランキング**\n{msg}")

    @app_commands.command(name="t_ranking", description="称号数ランキング")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def title_ranking(self, interaction: discord.Interaction):
        data = load_data()
        sorted_data = sorted(data.items(), key=lambda x: x[1].get("titles", 0), reverse=True)

        lines = []
        for i, (user_id, user_data) in enumerate(sorted_data, start=1):
            user = await self.bot.fetch_user(int(user_id))
            titles = user_data.get("titles", 0)
            lines.append(f"{i}. {user.name} - {titles}真")

        msg = "\n".join(lines) if lines else "ランキングデータがありません。"
        await interaction.response.send_message(f"👑 **称号数ランキング**\n{msg}")

    @app_commands.command(name="k_ranking", description="資産ランキング（称号換算）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def kumulative_ranking(self, interaction: discord.Interaction):
        data = load_data()
        sorted_data = sorted(data.items(), key=lambda x: x[1].get("coins", 0) + x[1].get("titles", 0) * 1000000, reverse=True)

        lines = []
        for i, (user_id, user_data) in enumerate(sorted_data, start=1):
            user = await self.bot.fetch_user(int(user_id))
            coins = user_data.get("coins", 0)
            titles = user_data.get("titles", 0)
            total = coins + titles * 10000
            lines.append(f"{i}. {user.name} - {total}枚（称号{titles}個＋残コイン{coins}枚）")

        msg = "\n".join(lines) if lines else "ランキングデータがありません。"
        await interaction.response.send_message(f"💰 **資産ランキング（称号換算）**\n{msg}")

async def setup(bot):
    await bot.add_cog(RankingCog(bot))
