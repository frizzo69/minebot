import discord
from discord.ext import commands
import aiohttp
import re

class Steal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="steal")
    @commands.has_permissions(manage_emojis=True)
    async def steal(self, ctx, emoji: str, *, name: str = None):
        """Adds an emoji to the server from another emoji/URL."""
        match = re.search(r'<(a?):(.+?):(\d+)>', emoji)
        if match:
            if not name: name = match.group(2)
            url = f"https://cdn.discordapp.com/emojis/{match.group(3)}.{'gif' if match.group(1) else 'png'}"
        elif emoji.startswith("http"):
            url, name = emoji, name or "stolen"
        else:
            return await ctx.send("❌ Provide a custom emoji or URL.")

        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                img = await r.read()
                new_emoji = await ctx.guild.create_custom_emoji(name=name, image=img)
                await ctx.send(f"✅ Added {new_emoji}")

async def setup(bot):
    await bot.add_cog(Steal(bot))