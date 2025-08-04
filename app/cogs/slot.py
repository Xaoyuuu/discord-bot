import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio

GUILD_ID = 1352701686812246086
DATA_FILE = "coins.json"

class Slot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()

        self.normal_symbols = ["®️", "🍇", "🍒", "🍊", "🚢", "♦️", "💩", "🔑", "⑦"]
        self.kakuhen_symbols = ["🚢", "♦️", "⑦", "真"]

        self.normal_distribution = {
            "®️": (1, 3, 3),
            "🍇": (1, 7, 8),
            "🍒": (1, 10, 15),
            "🍊": (1, 20, 30),
            "🚢": (1, 60, 100),
            "♦️": (1, 100, 150),
            "⑦": (1, 300, 300),
            "💩": (1, 3000, 3000),
            "🔑": (1, 100, 0),
        }

        self.kakuhen_distribution = {
            "🚢": (1, 5, 25),
            "♦️": (1, 15, 150),
            "⑦": (1, 60, 300),
            "💩": (1, 2000, 3000),
            "真": (1, 3000, 5000),
        }

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)
        with open(DATA_FILE, 'r') as f:
            return json.load(f)

    def save_data(self, data):
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def roll_symbol(self, kakuhen, target):
        dist = self.kakuhen_distribution if kakuhen else self.normal_distribution
        prob = dist[target][0] / dist[target][1]
        return random.random() < prob

    def choose_loser_symbol(self, kakuhen):
        symbols = self.kakuhen_symbols if kakuhen else self.normal_symbols
        while True:
            symbol = random.choice(symbols)
            if not self.roll_symbol(kakuhen, symbol):
                return symbol

    def spin(self, kakuhen):
        symbols = self.kakuhen_symbols if kakuhen else self.normal_symbols
        for sym in symbols:
            if self.roll_symbol(kakuhen, sym):
                return [sym] * 3
        for _ in range(100):
            res = [self.choose_loser_symbol(kakuhen) for _ in range(3)]
            if not (res[0] == res[1] == res[2]):
                return res
        return ["®️", "🍇", "🍒"]

    def get_reward(self, symbol, kakuhen):
        dist = self.kakuhen_distribution if kakuhen else self.normal_distribution
        return dist[symbol][2]

    @app_commands.command(name="slot", description="3コインでスロットを回す！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def slot(self, interaction: discord.Interaction):
        async with self.lock:
            user_id = str(interaction.user.id)
            data = self.load_data()

            user = data.get(user_id, {"coins": 0, "kakuhen": 0, "keys": 0})

            if user["coins"] < 3:
                await interaction.response.send_message("コインが足りません！", ephemeral=True)
                return

            user["coins"] -= 3
            kakuhen = user.get("kakuhen", 0)
            symbols = self.spin(kakuhen > 0)
            reward = 0
            msg = f"{'|'.join(symbols)}\n"

            if symbols[0] == symbols[1] == symbols[2]:
                sym = symbols[0]
                reward = self.get_reward(sym, kakuhen > 0)
                user["coins"] += reward
                msg += f"{sym}HIT！ {reward}枚GET！"

                if sym == "♦️":
                    user["kakuhen"] += 10
                    msg += f"\n🔥確変モード突入🔥（+10回転）"
                elif sym == "⑦":
                    user["kakuhen"] += 50
                    msg += f"\n🔥確変モード突入🔥（+50回転）"
                elif sym == "真":
                    title = user.get("title", 0) + 1
                    user["title"] = title
                    msg += f"\n🎉称号『真を揃えし者』 x{title}獲得！"
                elif sym == "💩":
                    user["kakuhen"] = 0
                    msg += "\n💩で確変終了..."
            else:
                for s in symbols:
                    if s == "💩":
                        msg += "ブリ！"
                    elif s == "🔑":
                        user["keys"] += 1
                        msg += f"🔑を発見！現在{user['keys']}/20"

                if user["keys"] >= 20:
                    user["keys"] = 0
                    user["kakuhen"] += 30
                    msg += "\n🔓20個達成！🔥確変モード突入🔥（30回転）"

            if kakuhen > 0:
                user["kakuhen"] -= 1
                msg += f"\n確変残り: {user['kakuhen']}回"

            data[user_id] = user
            self.save_data(data)
            await interaction.response.send_message(msg)

async def setup(bot):
    await bot.add_cog(Slot(bot))
