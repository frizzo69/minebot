import discord
from discord.ext import commands
import json
import os
import time

AFK_FILE = "afk_data.json"

def get_afk():
    if not os.path.exists(AFK_FILE): return {}
    with open(AFK_FILE, "r") as f: return json.load(f)

def save_afk(data):
    with open(AFK_FILE, "w") as f: json.dump(data, f, indent=4)

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="afk")
    async def afk(self, ctx, *, reason="AFK"):
        data = get_afk()
        # Added 'timestamp' to track when AFK started
        data[str(ctx.author.id)] = {"reason": reason, "time": time.time()}
        save_afk(data)
        await ctx.send(f"{ctx.author.name}, I set your AFK: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        data = get_afk()
        user_id = str(message.author.id)

        # Fix: Check if user is AFK and ensure they didn't JUST set it 
        # (ignores messages sent within 3 seconds of setting AFK)
        if user_id in data:
            afk_info = data[user_id]
            elapsed = time.time() - afk_info['time']

            if elapsed > 3: 
                data.pop(user_id)
                save_afk(data)

                duration = int(elapsed)
                m, s = divmod(duration, 60)
                h, m = divmod(m, 60)
                time_str = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

                await message.channel.send(f"Welcome back {message.author.name}, you were AFK for {time_str}.")

        # Notify if someone pings an AFK user
        for mention in message.mentions:
            if str(mention.id) in data:
                info = data[str(mention.id)]
                await message.channel.send(f"{mention.name} is AFK: {info['reason']} (since <t:{int(info['time'])}:R>)")

async def setup(bot):
    await bot.add_cog(AFK(bot))