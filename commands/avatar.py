import discord
from discord.ext import commands

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Displays a user's profile picture."""
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar for {member.display_name}", color=member.color)
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Link", value=f"[Open in Browser]({member.display_avatar.url})")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Avatar(bot))