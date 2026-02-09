import discord
from discord.ext import commands

class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Removing the default help command so ours works
        self.bot.remove_command('help')

    @commands.command(name="help", aliases=["commands", "h"])
    async def help_command(self, ctx):
        """Displays all available commands automatically."""

        embed = discord.Embed(
            title="🤖 Bot Commands List",
            description="Here are the available commands for this bot:",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        # Loop through all loaded Cogs
        for cog_name, cog in self.bot.cogs.items():
            # Get all commands in the cog
            command_list = cog.get_commands()
            if not command_list:
                continue

            # Format the commands: -name, -alias
            value = ""
            for cmd in command_list:
                # This grabs the docstring (the text under the command function)
                desc = cmd.help if cmd.help else "No description"
                value += f"`-{cmd.name}` - {desc}\n"

            if value:
                embed.add_field(name=f" {cog_name}", value=value, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))