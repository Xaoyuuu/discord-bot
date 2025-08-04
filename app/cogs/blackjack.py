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

def draw_card():
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    return random.choice(suits), random.choice(ranks)

def card_value(rank):
    if rank in ['J', 'Q', 'K']:
        return 10
    elif rank == 'A':
        return 11
    else:
        return int(rank)

def hand_value(cards):
    value = sum(card_value(rank) for _, rank in cards)
    aces = sum(1 for _, rank in cards if rank == 'A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

class BlackjackGame:
    def __init__(self, bet, user_cards, dealer_cards):
        self.bet = bet
        self.user_cards = user_cards
        self.dealer_cards = dealer_cards

class BlackjackFixed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    async def start_blackjack(self, interaction: discord.Interaction, bet: int):
        user_id = str(interaction.user.id)
        coins_data = load_coins()

        if user_id not in coins_data:
            coins_data[user_id] = {
                "username": interaction.user.name,
                "coins": 100,
                "key_count": 0,
                "kakuhen_turns": 0,
                "true_title_count": 0
            }

        user_data = coins_data[user_id]
        if bet > user_data["coins"]:
            await interaction.response.send_message("コインが足りません！", ephemeral=True)
            return

        # コイン減らす
        user_data["coins"] -= bet
        save_coins(coins_data)

        user_cards = [draw_card(), draw_card()]
        dealer_cards = [draw_card(), draw_card()]
        self.games[user_id] = BlackjackGame(bet, user_cards, dealer_cards)

        await self.show_game(interaction, interaction.user, user_cards, dealer_cards, first=True)

    async def show_game(self, interaction, user, user_cards, dealer_cards, first=False):
        user_value = hand_value(user_cards)

        view = discord.ui.View(timeout=60)

        hit_button = discord.ui.Button(label="ヒット", style=discord.ButtonStyle.primary)
        stand_button = discord.ui.Button(label="スタンド", style=discord.ButtonStyle.secondary)

        async def hit_callback(i: discord.Interaction):
            if i.user != user:
                await i.response.send_message("これはあなたのゲームですらないよ！", ephemeral=True)
                return
            self.games[str(i.user.id)].user_cards.append(draw_card())
            await self.check_game(i, user)

        async def stand_callback(i: discord.Interaction):
            if i.user != user:
                await i.response.send_message("これはあなたのゲームですらないよ！", ephemeral=True)
                return
            await self.dealer_turn(i, user)

        hit_button.callback = hit_callback
        stand_button.callback = stand_callback

        view.add_item(hit_button)
        view.add_item(stand_button)

        embed = discord.Embed(title="ブラックジャック", description=f"{user.mention} のターン")
        embed.add_field(name="あなたの手札", value=" / ".join(f"{s}{r}" for s, r in user_cards) + f" （{user_value}）", inline=False)
        embed.add_field(name="ディーラー", value=f"{dealer_cards[0][0]}{dealer_cards[0][1]} / ？？", inline=False)

        if first:
            await interaction.response.send_message(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=view)

    async def check_game(self, interaction, user):
        user_id = str(user.id)
        game = self.games[user_id]
        user_value = hand_value(game.user_cards)

        if user_value > 21:
            del self.games[user_id]
            await interaction.response.edit_message(
                content=f"{user.mention} バースト！負け！",
                embed=None, view=None
            )
        else:
            await self.show_game(interaction, user, game.user_cards, game.dealer_cards)

    async def dealer_turn(self, interaction, user):
        user_id = str(user.id)
        game = self.games[user_id]
        dealer_cards = game.dealer_cards
        user_cards = game.user_cards

        while hand_value(dealer_cards) < 17:
            dealer_cards.append(draw_card())

        dealer_value = hand_value(dealer_cards)
        user_value = hand_value(user_cards)

        coins_data = load_coins()
        payout = 0

        if dealer_value > 21 or user_value > dealer_value:
            payout = game.bet * 2
            result = f"{user.mention} 勝利！{payout}コインGET！"
        elif user_value == dealer_value:
            payout = game.bet
            result = f"{user.mention} 引き分け！{payout}コイン返却！"
        else:
            result = f"{user.mention} 負け…"

        coins_data[user_id]["coins"] += payout
        save_coins(coins_data)
        del self.games[user_id]

        embed = discord.Embed(title="ブラックジャック - 結果")
        embed.add_field(name="あなたの手札", value=" / ".join(f"{s}{r}" for s, r in user_cards) + f"（{user_value}）", inline=False)
        embed.add_field(name="ディーラーの手札", value=" / ".join(f"{s}{r}" for s, r in dealer_cards) + f"（{dealer_value}）", inline=False)
        embed.set_footer(text=f"現在のコイン：{coins_data[user_id]['coins']}")

        await interaction.response.edit_message(content=result, embed=embed, view=None)

    # 5つのコマンド
    @app_commands.command(name="blackjack1", description="ブラックジャック（1コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack1(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 1)

    @app_commands.command(name="blackjack10", description="ブラックジャック（10コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack10(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 10)

    @app_commands.command(name="blackjack100", description="ブラックジャック（100コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack100(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 100)

    @app_commands.command(name="blackjack500", description="ブラックジャック（500コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack500(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 500)

    @app_commands.command(name="blackjack1000", description="ブラックジャック（1000コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack1000(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 1000)

    @app_commands.command(name="blackjack10000", description="ブラックジャック（10000コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack10000(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 10000)     

    @app_commands.command(name="blackjack100000", description="ブラックジャック（100000コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack100000(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 100000)
    
    @app_commands.command(name="blackjack1000000", description="ブラックジャック（1000000コイン）")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def blackjack1000000(self, interaction: discord.Interaction):
        await self.start_blackjack(interaction, 1000000)
async def setup(bot):
    await bot.add_cog(BlackjackFixed(bot))
