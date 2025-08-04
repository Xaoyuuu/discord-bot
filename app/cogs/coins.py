import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
from datetime import datetime, timezone

GUILD_ID = 1352701686812246086
COIN_FILE = "coins.json"
DAILY_COINS = 3000

def load_data():
    if not os.path.exists(COIN_FILE):
        with open(COIN_FILE, "w") as f:
            json.dump({}, f)
    with open(COIN_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(COIN_FILE, "w") as f:
        json.dump(data, f, indent=4)

class CoinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_task.start()

    def cog_unload(self):
        self.daily_task.cancel()

    @tasks.loop(minutes=1)
    async def daily_task(self):
        now = datetime.now(timezone.utc).astimezone()
        # 0時ちょうどだけ実行（毎分起動でOK）
        if now.hour == 0 and now.minute == 0:
            data = load_data()
            updated = False
            for user_id, user_data in data.items():
                last_daily_str = user_data.get("last_daily")
                last_daily = None
                if last_daily_str:
                    last_daily = datetime.fromisoformat(last_daily_str)
                # 今日配布済みかチェック
                if not last_daily or last_daily.date() < now.date():
                    user_data["coins"] = user_data.get("coins", 0) + DAILY_COINS
                    user_data["last_daily"] = now.isoformat()
                    updated = True
            if updated:
                save_data(data)

    @app_commands.command(name="coin", description="所持コインと称号を確認")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def check_coin(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()

        if user_id not in data:
            data[user_id] = {"coins": DAILY_COINS, "titles": 0, "last_daily": None}
            save_data(data)

        user = data[user_id]
        coins = user.get("coins", 0)
        titles_count = user.get("titles", 0)

        if titles_count == 0:
            title = "なし"
        elif titles_count == 1:
            title = "真を揃えし者"
        else:
            title = f"{titles_count}真"

        await interaction.response.send_message(
            f"🪙 所持コイン: {coins}枚\n🏆 称号: {title}"
        )

async def setup(bot):
    await bot.add_cog(CoinCog(bot))