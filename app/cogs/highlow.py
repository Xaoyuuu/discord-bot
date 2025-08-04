import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

GUILD_ID = 1352701686812246086
COINS_FILE = "coins.json"

def load_coins():
    if not os.path.exists(COINS_FILE):
        with open(COINS_FILE, "w") as f:
            json.dump({}, f)
    with open(COINS_FILE, "r") as f:
        return json.load(f)

def save_coins(data):
    with open(COINS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def card_value(card):
    ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
             '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    return ranks[card]

def draw_card():
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    return random.choice(ranks)

class HighLowButtonView(discord.ui.View):
    def __init__(self, cog, user_id, bet, first_card):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.bet = bet
        self.first_card = first_card

    @discord.ui.button(label="ハイ", style=discord.ButtonStyle.success)
    async def high(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("これはあなたのゲームではありません！", ephemeral=True)
            return
        await interaction.response.defer()
        await self.cog.resolve_game(interaction, self.bet, self.first_card, True)
        self.stop()

    @discord.ui.button(label="ロー", style=discord.ButtonStyle.danger)
    async def low(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("これはあなたのゲームではありません！", ephemeral=True)
            return
        await interaction.response.defer()
        await self.cog.resolve_game(interaction, self.bet, self.first_card, False)
        self.stop()

class HighLowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="highlow", description="ハイアンドローで遊ぼう！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(amount="掛け金（正の整数）")
    async def highlow(self, interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        coins_data = load_coins()

        # 初期化
        if user_id not in coins_data:
            coins_data[user_id] = {
                "username": interaction.user.name,
                "coins": 100,
                "key_count": 0,
                "kakuhen_turns": 0,
                "true_title_count": 0
            }

        user = coins_data[user_id]

        if amount <= 0:
            await interaction.response.send_message("掛け金は1コイン以上にしてね！", ephemeral=True)
            return

        if user["coins"] < amount:
            await interaction.response.send_message("コインが足りません！", ephemeral=True)
            return

        user["coins"] -= amount
        save_coins(coins_data)

        first_card = draw_card()
        view = HighLowButtonView(self, user_id, amount, first_card)

        await interaction.response.send_message(
            f"🃏 最初のカードは **{first_card}** です。\nハイかローを選んでね！",
            view=view,
            ephemeral=True
        )

    async def resolve_game(self, interaction: discord.Interaction, bet: int, first_card: str, guess_high: bool):
        user_id = str(interaction.user.id)
        next_card = draw_card()
        first_val = card_value(first_card)
        next_val = card_value(next_card)

        # オッズ設定
        high_odds = {
            2: 1.4, 3: 1.4, 4: 1.5, 5: 1.6, 6: 1.8, 7: 2.0,
            8: 2.5, 9: 3.0, 10: 3.5, 11: 4.0, 12: 4.5, 13: 5.0, 14: 5.0
        }
        low_odds = {
            14: 1.4, 13: 1.4, 12: 1.5, 11: 1.6, 10: 1.8, 9: 2.0,
            8: 2.5, 7: 3.0, 6: 3.5, 5: 4.0, 4: 4.5, 3: 5.0, 2: 5.0
        }

        if next_val == first_val:
            result = "引き分け！掛け金は返却されます。"
            payout = bet
        else:
            win = (next_val > first_val and guess_high) or (next_val < first_val and not guess_high)
            if win:
                odds = high_odds.get(first_val, 2.0) if guess_high else low_odds.get(first_val, 2.0)
                payout = int(bet * odds)
                result = f"当たり！次のカードは **{next_card}** でした！倍率は {odds}倍！"
            else:
                payout = 0
                result = f"はずれ！次のカードは **{next_card}** でした。"

        coins_data = load_coins()
        user = coins_data[user_id]
        user["coins"] += payout
        save_coins(coins_data)

        await interaction.followup.send(
            f"🎲 {interaction.user.mention} のハイアンドロー結果 🎲\n"
            f"最初のカード: **{first_card}**\n"
            f"次のカード: **{next_card}**\n"
            f"{result}\n"
            f"掛け金: **{bet}** コイン\n"
            f"獲得: **{payout}** コイン\n"
            f"現在のコイン: **{user['coins']}** コイン"
        )

async def setup(bot):
    await bot.add_cog(HighLowCog(bot))
