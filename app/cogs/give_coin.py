import discord
from discord.ext import commands
from discord import app_commands
import json
import os

GUILD_ID = 1352701686812246086
COIN_FILE = "coins.json"

def load_coins():
    if not os.path.exists(COIN_FILE):
        with open(COIN_FILE, "w") as f:
            json.dump({}, f)
    with open(COIN_FILE, "r") as f:
        return json.load(f)

def save_coins(data):
    with open(COIN_FILE, "w") as f:
        json.dump(data, f, indent=4)

class GiveCoinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="givecoin", description="他のユーザーにコインを送る")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(user="コインをあげる相手", amount="送りたいコインの枚数")
    async def givecoin(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if user.id == interaction.user.id:
            await interaction.response.send_message("自分自身にコインは送れません！", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("1枚以上のコインを指定してね！", ephemeral=True)
            return

        sender_id = str(interaction.user.id)
        receiver_id = str(user.id)
        data = load_coins()

        if sender_id not in data:
            data[sender_id] = {"coins": 3000, "titles": 0, "last_daily": None}
        if receiver_id not in data:
            data[receiver_id] = {"coins": 3000, "titles": 0, "last_daily": None}

        sender_coins = data[sender_id]["coins"]

        if sender_coins < amount:
            await interaction.response.send_message(f"コインが足りません！（現在 {sender_coins}枚）", ephemeral=True)
            return

        data[sender_id]["coins"] -= amount
        data[receiver_id]["coins"] += amount

        save_coins(data)

        await interaction.response.send_message(
            f"{interaction.user.mention} が {user.mention} に {amount}枚のコインを送ったよ！"
        )

async def setup(bot):
    await bot.add_cog(GiveCoinCog(bot))
