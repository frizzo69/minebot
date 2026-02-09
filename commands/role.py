import discord
from discord.ext import commands

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="role", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx):
        """Manage roles. Use -role add or -role remove."""
        await ctx.send("❌ **Usage:** `-role add @user @role` or `-role remove @user @role`")

    @role.command(name="add")
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        """Adds a role to a member."""
        if role in member.roles:
            return await ctx.send(f"⚠️ {member.display_name} already has that role.")
        await member.add_roles(role)
        await ctx.send(f"✅ Added **{role.name}** to {member.mention}")

    @role.command(name="remove")
    async def remove(self, ctx, member: discord.Member, role: discord.Role):
        """Removes a role from a member."""
        if role not in member.roles:
            return await ctx.send(f"⚠️ {member.display_name} doesn't have that role.")
        await member.remove_roles(role)
        await ctx.send(f"✅ Removed **{role.name}** from {member.mention}")

async def setup(bot):
    await bot.add_cog(RoleManager(bot))