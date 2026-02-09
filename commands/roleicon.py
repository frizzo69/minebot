import discord
from discord.ext import commands
import aiohttp
import re

class RoleIcon(commands.Cog):
            def __init__(self, bot):
                self.bot = bot

            @commands.command(name="roleicon", aliases=["ri", "seticon"])
            @commands.has_permissions(manage_roles=True)
            async def role_icon(self, ctx, role: discord.Role, emoji_or_url: str = None):
                """Sets a role icon via attachment, emoji, or URL."""

                # Check for Level 2 Boost status
                if ctx.guild.premium_tier < 2:
                    return await ctx.send("⚠️ **Server Error:** Role icons require Server Boost Level 2.")

                # Priority 1: Image Attachment
                if ctx.message.attachments:
                    url = ctx.message.attachments[0].url
                    return await self.apply_icon_image(ctx, role, url)

                if not emoji_or_url:
                    return await ctx.send("❌ **Usage:** `-roleicon @Role <emoji/url/attachment>`")

                # Priority 2: Custom Discord Emoji (<:name:id>)
                custom_emoji = re.search(r'<a?:.+:(\d+)>', emoji_or_url)
                if custom_emoji:
                    eid = custom_emoji.group(1)
                    ext = "gif" if emoji_or_url.startswith("<a:") else "png"
                    url = f"https://cdn.discordapp.com/emojis/{eid}.{ext}?size=256"
                    return await self.apply_icon_image(ctx, role, url)

                # Priority 3: Standard Unicode Emoji (👑, 🔥)
                if not emoji_or_url.startswith("http"):
                    try:
                        await role.edit(unicode_emoji=emoji_or_url)
                        return await ctx.send(f"✅ Set {role.mention} icon to {emoji_or_url}")
                    except discord.HTTPException:
                        pass 

                # Priority 4: Image URL
                await self.apply_icon_image(ctx, role, emoji_or_url)

            async def apply_icon_image(self, ctx, role, url):
                """Helper to download and apply image-based icons."""
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                return await ctx.send("❌ Failed to download image from the provided source.")
                            img_data = await resp.read()

                    await role.edit(display_icon=img_data)
                    await ctx.send(f"✅ Successfully updated the icon for **{role.name}**!")

                except discord.Forbidden:
                    await ctx.send("❌ **Forbidden:** Check if my role is **ABOVE** the role I'm trying to edit.")
                except Exception as e:
                    await ctx.send(f"❌ **Error:** {e}")

            # --- THE ERROR HANDLER ---
            @role_icon.error
            async def role_icon_error(self, ctx, error):
                if isinstance(error, commands.MissingRequiredArgument):
                    # This triggers if they just type "-roleicon"
                    await ctx.send("❌ **Invalid Usage!**\nCorrect format: `-roleicon @Role <emoji or image>`")
                elif isinstance(error, commands.RoleNotFound):
                    # This triggers if they type a name that isn't a role
                    await ctx.send("❌ **Role Not Found!** Please mention the role or provide a valid Role ID.")
                elif isinstance(error, commands.MissingPermissions):
                    await ctx.send("❌ You don't have the `Manage Roles` permission to use this.")
                else:
                    # Logs other errors to console so you can see them
                    print(f"Unhandled error in roleicon: {error}")

async def setup(bot):
    await bot.add_cog(RoleIcon(bot))