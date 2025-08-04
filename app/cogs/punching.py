import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import json
import os

GUILD_ID = 1352701686812246086
SCORE_FILE = "scores.json"

class PunchingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_scores(self):
        if not os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, "w") as f:
                json.dump({}, f)
        with open(SCORE_FILE, "r") as f:
            return json.load(f)

    def save_scores(self, data):
        with open(SCORE_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def generate_score(self):
        roll = random.random()
        if roll < 1/8192:
            return 0, "🌑下界のさらに下、お前と知り合いだったとか恥ずかしい。大恥かいたわ。みんなに謝ってくれ。頼むから。人間界の恥か？人間界にすらいないか、下界の中でも底辺やもんな。お前より下ってあるの？てかお前誰？"
        elif roll < 2/8192:
            return 10000, "㊗️全ての真の生みの親　みんなあなたの子供です　天への道を突き進み　たどり着いたら真の園　その光景は他にない　あなたの真話続きます㊗️"
        elif roll < 0.20:
            score = random.randint(1, 30)
            return score, "🐀下界住！下水でも飲んでろ！"
        elif roll < 0.50:
            score = random.randint(31, 80)
            return score, "🙁普通の奴！なんにもないね、君って"
        elif roll < 0.65:
            score = random.randint(81, 120)
            return score, "🔥真！ようこそ"
        elif roll < 0.78:
            score = random.randint(121, 200)
            return score, "⚡２真！！ここまで来たか！"
        elif roll < 0.86:
            score = random.randint(201, 300)
            return score, "🌋５真！！！この景色は忘れない"
        elif roll < 0.91:
            score = random.randint(301, 400)
            return score, "🦍８真！！！！下界が見えづらいわ"
        elif roll < 0.94:
            score = random.randint(401, 600)
            return score, "💥伝説の１０真！！！！！"
        elif roll < 0.96:
            score = random.randint(601, 800)
            return score, "🌟伝説を超えた伝説の２０真"
        elif roll < 0.97:
            score = random.randint(801, 1000)
            return score, "🚀前人未到、３０真！新たな伝説が始まる"
        elif roll < 0.98:
            score = random.randint(1001, 1500)
            return score, "👹４０真！ここまで来るものはいる？"
        elif roll < 0.99:
            score = random.randint(1501, 2000)
            return score, "🔥５０真！伝説はさらに続く"
        elif roll < 0.996:
            score = random.randint(2001, 3000)
            return score, "✨70真！！この男、伝説につき"
        elif roll < 0.999:
            score = random.randint(3001, 5000)
            return score, "🌠９０真！！！！"
        else:
            score = random.randint(5001, 9999)
            return score, "🌈１００真！語ることなし"

    @app_commands.command(name="opunching_machine", description="殴ってスコアを出そう！最大20発まで指定できるよ！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(count="何発殴る？1〜20の範囲で指定してね")
    async def punching(self, interaction: discord.Interaction, count: int = 1):
        if count < 1 or count > 20:
            await interaction.response.send_message("1から20までの回数を指定してね！", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        scores = self.load_scores()

        if user_id not in scores or not isinstance(scores[user_id], dict):
            scores[user_id] = {
                "username": interaction.user.name,
                "count": 0,
                "total_score": 0,
                "high_score": 0
            }

        user_data = scores[user_id]
        results = []

        for _ in range(count):
            score, comment = self.generate_score()
            user_data["count"] += 1
            user_data["total_score"] += score
            if score > user_data["high_score"]:
                user_data["high_score"] = score
            results.append(f"スコア: {score}\n{comment}")

        self.save_scores(scores)

        message = f"{interaction.user.mention} のパンチ結果（{count}発）:\n" + "\n\n".join(results)
        await interaction.response.send_message(message)

    @app_commands.command(name="myscore", description="自分のパンチ履歴を見る")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def myscore(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        scores = self.load_scores()

        if user_id not in scores:
            await interaction.response.send_message("まだプレイしてないよ！")
            return

        data = scores[user_id]
        avg = data["total_score"] / data["count"] if data["count"] > 0 else 0

        await interaction.response.send_message(
            f"🔨 あなたのパンチ履歴：\n"
            f"回数: {data['count']}\n"
            f"平均スコア: {avg:.2f}\n"
            f"ハイスコア: {data['high_score']}"
        )

    @app_commands.command(name="ranking", description="ハイスコアランキング表示！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ranking(self, interaction: discord.Interaction):
        scores = self.load_scores()
        valid_scores = {uid: data for uid, data in scores.items() if isinstance(data, dict)}

        ranking_data = sorted(
            valid_scores.items(),
            key=lambda item: item[1]["high_score"],
            reverse=True
        )

        msg = "**🥇 ハイスコアランキングTOP10：**\n"
        for i, (uid, data) in enumerate(ranking_data[:10], start=1):
            msg += f"{i}. {data['username']} - ハイスコア: {data['high_score']}（回数: {data['count']}）\n"

        await interaction.response.send_message(msg)

    @app_commands.command(name="a_ranking", description="平均スコアランキング表示！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def a_ranking(self, interaction: discord.Interaction):
        scores = self.load_scores()
        valid_scores = {uid: data for uid, data in scores.items() if isinstance(data, dict)}

        ranking_data = sorted(
            valid_scores.items(),
            key=lambda item: (item[1]["total_score"] / item[1]["count"]) if item[1]["count"] > 0 else 0,
            reverse=True
        )

        msg = "**📊 平均スコアランキングTOP10：**\n"
        for i, (uid, data) in enumerate(ranking_data[:10], start=1):
            avg = data["total_score"] / data["count"]
            msg += f"{i}. {data['username']} - 平均スコア: {avg:.2f}（回数: {data['count']}）\n"

        await interaction.response.send_message(msg)

    @app_commands.command(name="p_ranking", description="叩いた回数ランキング表示！")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def p_ranking(self, interaction: discord.Interaction):
        scores = self.load_scores()
        valid_scores = {uid: data for uid, data in scores.items() if isinstance(data, dict)}

        ranking_data = sorted(
            valid_scores.items(),
            key=lambda item: item[1]["count"],
            reverse=True
        )

        msg = "**🔨 叩いた回数ランキングTOP10：**\n"
        for i, (uid, data) in enumerate(ranking_data[:10], start=1):
            msg += f"{i}. {data['username']} - 回数: {data['count']} ハイスコア: {data['high_score']}\n"

        await interaction.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(PunchingCog(bot))
