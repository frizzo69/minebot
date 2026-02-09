import discord
from discord.ext import commands
from datetime import datetime
import collections

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Stores a list of the last 5 deleted messages per channel ID
        self.snipes = collections.defaultdict(lambda: collections.deque(maxlen=5))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        # Add message info to the channel's history
        self.snipes[message.channel.id].appendleft({
            "content": message.content or "[No Text Content]",
            "author": message.author,
            "time": datetime.now()
        })

    @commands.command(name="snipe")
    async def snipe(self, ctx):
        """Shows the very last deleted message in an embed."""
        channel_snipes = self.snipes.get(ctx.channel.id)

        if not channel_snipes:
            return await ctx.send("Nothing to snipe here!")

        msg = channel_snipes[0] # Get the most recent one

        embed = discord.Embed(
            description=f"In **{ctx.channel.mention}**, <t:{int(msg['time'].timestamp())}:R>",
            color=discord.Color.blue()
        )
        embed.set_author(name=msg['author'].name, icon_url=msg['author'].display_avatar.url)
        embed.add_field(name="Message:", value=msg['content'], inline=False)
        embed.set_footer(text=f"Deleted at | {msg['time'].strftime('%I:%M %p')}")

        await ctx.send(embed=embed)

    @commands.command(name="snipeall")
    async def snipeall(self, ctx):
        """Shows multiple recently deleted messages in an embed list."""
        channel_snipes = self.snipes.get(ctx.channel.id)

        if not channel_snipes:
            return await ctx.send("No recent snipes found in this channel!")

        embed = discord.Embed(
            title=f"Sniped messages in #{ctx.channel.name}",
            color=discord.Color.blue()
        )

        description_lines = []
        for msg in channel_snipes:
            timestamp = f"<t:{int(msg['time'].timestamp())}:R>"
            line = f"{msg['author'].mention}, deleted {timestamp}: {msg['content']}"
            description_lines.append(line)

        embed.description = "\n".join(description_lines)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Snipe(bot))