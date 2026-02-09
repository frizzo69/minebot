import discord
from discord.ext import commands

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx):
        old_channel = ctx.channel
        author = ctx.author

        # Clone and move to the same position
        new_channel = await old_channel.clone(reason=f"Nuked by {author}")
        await new_channel.edit(position=old_channel.position)

        # Delete old channel
        await old_channel.delete()

        # Plain text notification
        await new_channel.send(f"**Channel nuked by {author.mention}**")

async def setup(bot):
    await bot.add_cog(Nuke(bot))