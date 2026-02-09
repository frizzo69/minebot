import discord
from discord.ext import commands

class RoleInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roleinfo", aliases=["ri_info"])
    async def roleinfo(self, ctx, role: discord.Role):
        """Displays details of a specific role."""
        embed = discord.Embed(title=f"Role: {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Members", value=len(role.members))
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Hoisted", value=role.hoist)
        embed.set_footer(text=f"Created: {role.created_at.strftime('%Y-%m-%d')}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleInfo(bot))