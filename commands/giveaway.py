import discord
from discord.ext import commands, tasks
import random
import asyncio
import json
import os
import time
import re

GIVEAWAY_FILE = "giveaways.json"

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Start the background task
        self.check_giveaways.start()
        if not os.path.exists(GIVEAWAY_FILE):
            with open(GIVEAWAY_FILE, "w") as f:
                json.dump([], f)

    def cog_unload(self):
        self.check_giveaways.cancel()

    def parse_time(self, time_str):
        units = {
            "s": 1,
            "min": 60,
            "h": 3600,
            "d": 86400,
            "m": 2592000, 
            "y": 31536000 
        }
        match = re.match(r"(\d+)([a-z]+)", time_str.lower())
        if not match: return None
        amount, unit = match.groups()
        return int(amount) * units.get(unit, 0)

    def get_data(self):
        try:
            with open(GIVEAWAY_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def save_data(self, data):
        with open(GIVEAWAY_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        """Checks every 10 seconds if a giveaway should end."""
        now = time.time()
        data = self.get_data()
        if not data:
            return

        active_giveaways = []
        for g in data:
            if now >= g["end_time"]:
                print(f"⏰ Time up for giveaway: {g['prize']}")
                await self.end_giveaway(g)
            else:
                active_giveaways.append(g)

        self.save_data(active_giveaways)

    async def end_giveaway(self, g):
        channel = self.bot.get_channel(g["channel_id"])
        if not channel: return

        try:
            msg = await channel.fetch_message(g["msg_id"])
        except: return

        # Get users who reacted with 🎉
        users = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)

        if not users:
            await channel.send(f"❌ No one joined the giveaway for **{g['prize']}**.")
            embed = msg.embeds[0]
            embed.description = "No winners (no entries)."
            await msg.edit(content="🎊 **GIVEAWAY ENDED** 🎊", embed=embed)
        else:
            winners_count = min(len(users), g["winners"])
            winners = random.sample(users, winners_count)
            winner_mentions = ", ".join([w.mention for w in winners])

            await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{g['prize']}**!")

            embed = msg.embeds[0]
            embed.description = f"**Winners:** {winner_mentions}\n**Hosted by:** <@{g['host_id']}>"
            embed.color = discord.Color.dark_grey()
            await msg.edit(content="🎊 **GIVEAWAY ENDED** 🎊", embed=embed)

    @commands.command(name="gstart")
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):
        seconds = self.parse_time(duration)
        if not seconds: 
            return await ctx.send("❌ Format: `-gstart 10m 1 Nitro`. Units: `s, min, h, d, m, y`")

        end_timestamp = int(time.time() + seconds)

        embed = discord.Embed(
            title="🎉 NEW GIVEAWAY 🎉",
            description=f"Prize: **{prize}**\nEnds: <t:{end_timestamp}:R> (<t:{end_timestamp}:f>)\nWinners: **{winners}**",
            color=discord.Color.blue()
        )
        embed.set_footer(text="React with 🎉 to enter!")

        msg = await ctx.send(content="🎊 **GIVEAWAY START** 🎊", embed=embed)
        await msg.add_reaction("🎉")

        data = self.get_data()
        data.append({
            "msg_id": msg.id,
            "channel_id": ctx.channel.id,
            "end_time": float(end_timestamp),
            "winners": winners,
            "prize": prize,
            "host_id": ctx.author.id
        })
        self.save_data(data)

    @commands.command(name="gextend")
    @commands.has_permissions(manage_guild=True)
    async def gextend(self, ctx, msg_id: int, extra_time: str):
        added_seconds = self.parse_time(extra_time)
        if not added_seconds: return await ctx.send("❌ Invalid time unit.")

        data = self.get_data()
        found = False
        for g in data:
            if g["msg_id"] == msg_id:
                g["end_time"] += added_seconds
                new_end = int(g["end_time"])

                # Update Message
                try:
                    channel = self.bot.get_channel(g["channel_id"])
                    msg = await channel.fetch_message(msg_id)
                    embed = msg.embeds[0]
                    embed.description = f"Prize: **{g['prize']}**\nEnds: <t:{new_end}:R> (<t:{new_end}:f>)\nWinners: **{g['winners']}**"
                    await msg.edit(embed=embed)
                    found = True
                except:
                    return await ctx.send("❌ Found the giveaway in data, but couldn't find the Discord message.")

        if found:
            self.save_data(data)
            await ctx.send(f"✅ Giveaway extended by `{extra_time}`.")
        else:
            await ctx.send("❌ Giveaway not found. Is it already over?")

    @commands.command(name="greroll")
    @commands.has_permissions(manage_guild=True)
    async def greroll(self, ctx, msg_id: int):
        try:
            msg = await ctx.channel.fetch_message(msg_id)
            users = []
            for reaction in msg.reactions:
                if str(reaction.emoji) == "🎉":
                    async for user in reaction.users():
                        if not user.bot:
                            users.append(user)

            if not users: return await ctx.send("❌ No one to reroll from.")
            winner = random.choice(users)
            await ctx.send(f"🎉 **New Winner:** {winner.mention}! Congratulations!")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(Giveaway(bot))