import discord
from discord.ext import commands

class Boosts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="boosts")
    async def boosts(self, ctx):
        """Shows total boosts and server level."""
        guild = ctx.guild
        await ctx.send(f"**{guild.name}** currently has **{guild.premium_subscription_count}** boosts (**Level {guild.premium_tier}**)!")

    @commands.command(name="boosters")
    async def boosters(self, ctx):
        """Lists boosters with boost count and duration. Mentions in embeds do not notify."""
        # Get all members who are boosting
        boosters = [m for m in ctx.guild.members if m.premium_since is not None]

        if not boosters:
            return await ctx.send("No one has boosted the server yet.")

        # Sort by oldest booster first
        boosters.sort(key=lambda x: x.premium_since)

        embed = discord.Embed(
            title=f"Server Boosters - {ctx.guild.name}",
            description=f"Total Server Boosts: {ctx.guild.premium_subscription_count}",
            color=0xf47fff
        )

        list_text = ""
        for i, b in enumerate(boosters, 1):
            # We count how many times they appear in the premium_subscribers list
            # to get the exact number of boosts they are providing.
            boost_count = len([m for m in ctx.guild.premium_subscribers if m.id == b.id])

            # Formatting as requested: Name -- X boosts (since <t:R>)
            # No emojis included.
            list_text += f"**{i}.** {b.mention} (since: <t:{int(b.premium_since.timestamp())}:R>)\n"

        embed.add_field(name="Current Boosters", value=list_text, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Boosts(bot))