import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os
from datetime import datetime, timezone

GUILD_ID = 1352701686812246086
COIN_FILE = "coins.json"
LOTTO_FILE = "lotto_data.json"

DAILY_COINS = 1000
LOTTO_COST = 50
MINILOTO_COST = 10

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

class LottoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_task.start()

    def cog_unload(self):
        self.daily_task.cancel()

    @tasks.loop(minutes=1)
    async def daily_task(self):
        now = datetime.now(timezone.utc).astimezone()
        if now.hour == 0 and now.minute == 0:
            lotto_data = load_json(LOTTO_FILE)
            coins_data = load_json(COIN_FILE)

            today = now.date().isoformat()

            # 当選番号決定
            lotto_data["last_draw_date"] = today
            lotto_data["lotto7_numbers"] = random.sample(range(1,38),7)
            lotto_data["miniloto_numbers"] = random.sample(range(1,30),5)

            save_json(LOTTO_FILE, lotto_data)
            save_json(COIN_FILE, coins_data)
            print(f"[{today}] ロト抽選実施！")

    @app_commands.command(name="loto_check", description="自分の購入したロトの抽選結果を確認")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def loto_check(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        coins_data = load_json(COIN_FILE)
        lotto_data = load_json(LOTTO_FILE)

        if user_id not in coins_data:
            await interaction.response.send_message("コインデータが見つかりません。")
            return

        user = coins_data[user_id]
        purchases = user.get("lotto_purchases", {})

        if not purchases:
            await interaction.response.send_message("購入履歴がありません。")
            return

        lotto7_numbers = set(lotto_data.get("lotto7_numbers", []))
        miniloto_numbers = set(lotto_data.get("miniloto_numbers", []))

        total_payout = 0
        message_lines = []

        dates_to_remove = []

        payout_lotto7 = {7:50000000,6:20000,5:8000,4:800,3:100,2:40,1:2}
        payout_miniloto = {5:30000,4:200,3:10,2:5,1:5}

        # 今日までの購入履歴を全部抽選対象に
        dates_to_check = []
        today_date = datetime.now(timezone.utc).astimezone().date()
        for date_str in list(purchases.keys()):
            purchase_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if purchase_date <= today_date:
                dates_to_check.append(date_str)

        for date_str in dates_to_check:
            purchase_day = purchases[date_str]
            # ロト7処理
            for entry in purchase_day.get("lotto7", []):
                nums = set(entry["numbers"])
                count = entry["count"]
                hits = len(nums & lotto7_numbers)
                payout = payout_lotto7.get(hits, 0) * count
                total_payout += payout
                message_lines.append(f"【{date_str}】ロト7 {entry['numbers']} → {hits}個的中！ 配当: {payout}コイン")

            # ミニロト処理
            for entry in purchase_day.get("miniloto", []):
                nums = set(entry["numbers"])
                count = entry["count"]
                hits = len(nums & miniloto_numbers)
                payout = payout_miniloto.get(hits, 0) * count
                total_payout += payout
                message_lines.append(f"【{date_str}】ミニロト {entry['numbers']} → {hits}個的中！ 配当: {payout}コイン")

            # 抽選済み＆払い出し済みだから履歴削除対象
            dates_to_remove.append(date_str)

        # 合計払い出しを加算
        user["coins"] = user.get("coins", 0) + total_payout

        # 削除処理
        for date_str in dates_to_remove:
            if date_str in purchases:
                del purchases[date_str]

        save_json(COIN_FILE, coins_data)

        if total_payout > 0:
            message_lines.append(f"合計払い出し: {total_payout}コインを追加しました！")
        else:
            message_lines.append("残念ながら当選はありませんでした。")

        await interaction.response.send_message("\n".join(message_lines))

    @app_commands.command(name="loto_random", description="ロト7 ランダム数字を指定口数購入")
    @app_commands.describe(
        count="購入口数（1口50枚）"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def loto_random(self, interaction: discord.Interaction, count: int):
        user_id = str(interaction.user.id)
        coins_data = load_json(COIN_FILE)

        if user_id not in coins_data:
            coins_data[user_id] = {"coins": DAILY_COINS, "titles":0}
        user = coins_data[user_id]

        total_cost = LOTTO_COST * count
        if user.get("coins",0) < total_cost:
            await interaction.response.send_message(f"コインが足りません。{total_cost}枚必要です。")
            return

        user["coins"] -= total_cost

        if "lotto_purchases" not in user:
            user["lotto_purchases"] = {}

        today = datetime.now(timezone.utc).astimezone().date().isoformat()
        if today not in user["lotto_purchases"]:
            user["lotto_purchases"][today] = {"lotto7":[], "miniloto":[]}

        for _ in range(count):
            nums = random.sample(range(1,31),7)
            user["lotto_purchases"][today]["lotto7"].append({"numbers": nums, "count": 1})

        save_json(COIN_FILE, coins_data)

        await interaction.response.send_message(f"ロト7 ランダム数字を{count}口購入しました！（合計 {total_cost}コイン消費）")

    @app_commands.command(name="miniloto_random", description="ミニロト ランダム数字を指定口数購入")
    @app_commands.describe(
        count="購入口数（1口10枚）"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def miniloto_random(self, interaction: discord.Interaction, count: int):
        user_id = str(interaction.user.id)
        coins_data = load_json(COIN_FILE)

        if user_id not in coins_data:
            coins_data[user_id] = {"coins": DAILY_COINS, "titles":0}
        user = coins_data[user_id]

        total_cost = MINILOTO_COST * count
        if user.get("coins",0) < total_cost:
            await interaction.response.send_message(f"コインが足りません。{total_cost}枚必要です。")
            return

        user["coins"] -= total_cost

        if "lotto_purchases" not in user:
            user["lotto_purchases"] = {}

        today = datetime.now(timezone.utc).astimezone().date().isoformat()
        if today not in user["lotto_purchases"]:
            user["lotto_purchases"][today] = {"lotto7":[], "miniloto":[]}

        for _ in range(count):
            nums = random.sample(range(1,14),5)
            user["lotto_purchases"][today]["miniloto"].append({"numbers": nums, "count": 1})

        save_json(COIN_FILE, coins_data)

        await interaction.response.send_message(f"ミニロト ランダム数字を{count}口購入しました！（合計 {total_cost}コイン消費）")

async def setup(bot):
    await bot.add_cog(LottoCog(bot))
