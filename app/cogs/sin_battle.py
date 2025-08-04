import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random

GUILD_ID = 1352701686812246086
COIN_FILE = "coins.json"

def load_data() -> dict:
    if not os.path.exists(COIN_FILE):
        with open(COIN_FILE, "w") as f:
            json.dump({}, f)
    with open(COIN_FILE, "r") as f:
        return json.load(f)

def save_data(data: dict) -> None:
    with open(COIN_FILE, "w") as f:
        json.dump(data, f, indent=4)

class DiceRollView(discord.ui.View):
    def __init__(self, cog, interaction, user_id, amount, enemy, player_name):
        super().__init__(timeout=120)
        self.cog = cog
        self.interaction = interaction
        self.user_id = user_id
        self.amount = amount
        self.enemy = enemy
        self.rolls = []
        self.message = None
        self.player_name = player_name

    @discord.ui.button(label="サイコロを振る", style=discord.ButtonStyle.primary)
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ これはあなたのバトルではありません。", ephemeral=True)
            return

        roll = random.randint(1, 6)
        self.rolls.append(roll)

        await interaction.response.defer()
        await self.message.edit(content=self._build_message())

        if len(self.rolls) == 3:
            # バトル終了処理
            for child in self.children:
                child.disabled = True
            await self.message.edit(view=self)

            await self._finish_game()
            self.stop()

    def _build_message(self):
        enemy_rolls = ", ".join(map(str, self.enemy["rolls"]))
        enemy_total = sum(self.enemy["rolls"])
        player_rolls = ", ".join(map(str, self.rolls)) if self.rolls else "まだ振っていません"
        player_total = sum(self.rolls) if self.rolls else 0

        return (
            f"👾 敵：**{self.enemy['name']}**（ダイス{self.enemy['dice']}個、倍率x{self.enemy['multiplier']}）\n"
            f"👾 敵の出目：{enemy_rolls}（合計: {enemy_total}）\n"
            f"🎲 {self.player_name} の出目：{player_rolls}（合計: {player_total}）\n"
            f"🎲 『サイコロを振る』ボタンで1個ずつ振ってね！"
        )

    async def _finish_game(self):
        user_total = sum(self.rolls)
        enemy_total = sum(self.enemy["rolls"])
        data = load_data()
        user = data.get(self.user_id, {"titles": 0})

        result_msg = ""
        if user_total > enemy_total:
            win_amount = self.amount * self.enemy["multiplier"]
            user["titles"] += win_amount - self.amount
            result_msg = f"🏆 {self.player_name} の勝利！ {self.amount}真 → {win_amount}真！"
        elif user_total < enemy_total:
            user["titles"] -= self.amount
            result_msg = f"💥 {self.player_name} の敗北… {self.amount}真を失った。"
        else:
            result_msg = f"🤝 引き分け！ {self.player_name} の称号は変わらず。"

        data[self.user_id] = user
        save_data(data)

        await self.message.edit(content=self._build_message() + f"\n\n**{result_msg}**", view=self)


class SinBattle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sin_battle", description="PvEで称号『真』をかけてダイスバトル！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(amount="かける称号の数")
    async def sin_battle(self, interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        player_name = interaction.user.display_name
        data = load_data()

        if user_id not in data:
            await interaction.response.send_message("❌ データがありません。先にコマンドで称号をゲットしてね！", ephemeral=True)
            return

        user = data[user_id]
        titles = user.get("titles", 0)

        if amount <= 0:
            await interaction.response.send_message("❌ 1以上で賭けてね。", ephemeral=True)
            return

        if titles < amount:
            await interaction.response.send_message(f"❌ 称号が足りません！所持：{titles}真", ephemeral=True)
            return

        # 敵を決定
        enemies = [
            {"name": "無名の王", "dice": 2, "multiplier": 2},
            {"name": "tasty-melon", "dice": 3, "multiplier": 3},
            {"name": "inabaUR", "dice": 4, "multiplier": 4},
            {"name": "Havok", "dice": 5, "multiplier": 5},
        ]
        enemy = random.choice(enemies)
        enemy["rolls"] = [random.randint(1, 6) for _ in range(enemy["dice"])]

        view = DiceRollView(self, interaction, user_id, amount, enemy, player_name)
        await interaction.response.send_message(view._build_message(), view=view)
        view.message = await interaction.original_response()

async def setup(bot: commands.Bot):
    await bot.add_cog(SinBattle(bot))
