import discord
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="serverinfo", aliases=["si"])
    async def serverinfo(self, ctx):
        """Displays stats about the server."""
        g = ctx.guild
        embed = discord.Embed(title=g.name, color=discord.Color.blue())
        if g.icon: embed.set_thumbnail(url=g.icon.url)

        embed.add_field(name="Owner", value=g.owner.mention)
        embed.add_field(name="Members", value=g.member_count)
        embed.add_field(name="Boosts", value=f"Level {g.premium_tier} ({g.premium_subscription_count} boosts)")
        embed.set_footer(text=f"ID: {g.id} | Created: {g.created_at.strftime('%Y-%m-%d')}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))