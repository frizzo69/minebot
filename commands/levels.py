import discord
from discord.ext import commands
import json
import os
import random
import time
import math
import io
from easy_pil import Editor, load_image, Font

LEVEL_FILE = "levels.json"

def get_lvl_data():
    if not os.path.exists(LEVEL_FILE):
        return {"users": {}, "whitelisted_channels": [], "lvl_up_channel": None}
    with open(LEVEL_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"users": {}, "whitelisted_channels": [], "lvl_up_channel": None}

def save_lvl_data(data):
    with open(LEVEL_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_control = {}

    def get_xp_for_level(self, level):
        return 100 * (level ** 2)

    def get_level_from_xp(self, xp):
        if xp <= 0: return 0
        return int(math.sqrt(xp / 100))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        data = get_lvl_data()

        if message.channel.id not in data.get("whitelisted_channels", []): return

        user_id = str(message.author.id)
        current_time = time.time()

        if current_time - self.spam_control.get(user_id, 0) < 3: return

        user_data = data["users"].get(user_id, {"xp": 0, "level": 0})
        old_level = user_data["level"]

        user_data["xp"] += random.randint(15, 25)
        user_data["level"] = self.get_level_from_xp(user_data["xp"])
        self.spam_control[user_id] = current_time

        if user_data["level"] > old_level:
            lvl_msg = f"🎉 {message.author.mention}, you reached **Level {user_data['level']}**!"
            target_id = data.get("lvl_up_channel")
            ch = self.bot.get_channel(target_id) if target_id else message.channel
            await ch.send(lvl_msg)

        data["users"][user_id] = user_data
        save_lvl_data(data)

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        """Displays the rank card for a user."""
        member = member or ctx.author
        data = get_lvl_data()
        user_data = data["users"].get(str(member.id), {"xp": 0, "level": 0})

        current_xp = user_data["xp"]
        current_level = user_data["level"]
        xp_needed = self.get_xp_for_level(current_level + 1)
        xp_start = self.get_xp_for_level(current_level)

        progress = ((current_xp - xp_start) / (xp_needed - xp_start)) * 100 if (xp_needed - xp_start) > 0 else 0

        # Create Rank Card
        background = Editor(size=(900, 300)).canvas(color="#23272A")

        try:
            # Stable avatar loading
            avatar_url = member.display_avatar.replace(format="png", size=256).url
            avatar_img = await load_image(avatar_url)
            avatar = Editor(avatar_img).resize((150, 150)).circle_image()
            background.paste(avatar, (50, 75))
        except Exception as e:
            print(f"Avatar error: {e}")

        # Text and Bar
        font_big = Font.poppins(size=40, variant="bold")
        font_small = Font.poppins(size=30, variant="light")

        background.text((230, 100), str(member.name), font=font_big, color="white")
        background.text((230, 150), f"Level {current_level}", font=font_small, color="#3498db")
        background.text((850, 150), f"{current_xp} / {xp_needed} XP", font=font_small, color="white", align="right")
        background.bar((230, 210), max_width=600, height=30, percentage=progress, fill="#3498db", back_fill="#484B4E")

        file = discord.File(fp=background.image_bytes, filename="rank.png")
        await ctx.send(file=file)

    @commands.command(name="givexp")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx, member: discord.Member, amount: int):
        """Gives XP to a user and updates level automatically."""
        data = get_lvl_data()
        user_id = str(member.id)

        # Initialize user if they don't exist in data
        if user_id not in data["users"]:
            data["users"][user_id] = {"xp": 0, "level": 0}

        data["users"][user_id]["xp"] += amount
        data["users"][user_id]["level"] = self.get_level_from_xp(data["users"][user_id]["xp"])

        save_lvl_data(data)
        await ctx.send(f"✅ Added **{amount} XP** to {member.mention}. They are now **Level {data['users'][user_id]['level']}**.")

    # --- OTHER SETTINGS ---
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setxpchannel(self, ctx, channel: discord.TextChannel):
        data = get_lvl_data()
        if channel.id not in data["whitelisted_channels"]:
            data["whitelisted_channels"].append(channel.id)
            save_lvl_data(data)
            await ctx.send(f"✅ XP enabled in {channel.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removexpchannel(self, ctx, channel: discord.TextChannel):
        data = get_lvl_data()
        if channel.id in data["whitelisted_channels"]:
            data["whitelisted_channels"].remove(channel.id)
            save_lvl_data(data)
            await ctx.send(f"❌ XP disabled in {channel.mention}.")

async def setup(bot):
    await bot.add_cog(Levels(bot))