import discord
from discord.ext import commands
from discord import app_commands
import json
import os

GUILD_ID = 1352701686812246086
COIN_FILE = "coins.json"
EXCHANGE_COST = 1000000

def load_data():
    if not os.path.exists(COIN_FILE):
        with open(COIN_FILE, "w") as f:
            json.dump({}, f)
    with open(COIN_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(COIN_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ExchangeTitle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="exchange_title", description="コインを使って称号『真を揃えし者』を交換")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(count="交換する称号の数（1個 = 100万コイン）")
    async def exchange_title(self, interaction: discord.Interaction, count: int):
        if count <= 0:
            await interaction.response.send_message("❌ 1以上の数を指定してね", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            data[user_id] = {"coins": 0, "titles": 0, "last_daily": None}

        user = data[user_id]
        coins = user.get("coins", 0)
        total_cost = EXCHANGE_COST * count

        if coins < total_cost:
            await interaction.response.send_message(
                f"❌ コインが足りません（{count}個交換するには {total_cost}枚必要）", ephemeral=True
            )
            return

        user["coins"] -= total_cost
        user["titles"] = user.get("titles", 0) + count
        save_data(data)

        await interaction.response.send_message(
            f"✅ {count}個の称号「真を揃えし者」と交換しました！\n"
            f"🪙 残りコイン: {user['coins']}枚\n"
            f"🏆 現在の称号数: {user['titles']}真"
        )

async def setup(bot):
    await bot.add_cog(ExchangeTitle(bot))
