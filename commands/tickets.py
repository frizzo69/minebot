import discord
import json
import os
import asyncio
import io
from datetime import datetime
from discord.ext import commands
from discord.ui import Button, View, Select

# --- JSON Database Handler ---
CONFIG_FILE = "ticket_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Default Config Structure
        default_config = {
            "open_category_id": 0,
            "claim_category_id": 0,
            "transcript_channel_id": 0,
            "support_role_id": 0,
            "max_tickets_per_user": 1,
            "ticket_counter": 0
        }
        save_config(default_config)
        return default_config
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# --- HTML Transcript Generator (Simple Version) ---
def generate_transcript(messages, ticket_name, closer):
    html = f"""
    <html>
    <head><title>Transcript - {ticket_name}</title>
    <style>
        body {{ background-color: #36393f; color: #dcddde; font-family: sans-serif; padding: 20px; }}
        .msg {{ display: flex; margin-bottom: 10px; }}
        .content {{ margin-left: 10px; }}
        .author {{ font-weight: bold; color: #fff; }}
        .timestamp {{ font-size: 0.8em; color: #72767d; margin-left: 5px; }}
    </style>
    </head>
    <body>
    <h2>Transcript for {ticket_name}</h2>
    <p>Closed by: {closer} ({closer.id})</p>
    <hr>
    """
    for msg in reversed(messages):
        if msg.content or msg.attachments:
            content = msg.content
            if msg.attachments:
                content += f" <br><em>[Attachment: {msg.attachments[0].filename}]</em>"
            html += f"""
            <div class="msg">
                <div class="content">
                    <span class="author">{msg.author} ({msg.author.id})</span>
                    <span class="timestamp">{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}</span><br>
                    {content}
                </div>
            </div>
            """
    html += "</body></html>"
    return io.BytesIO(html.encode('utf-8'))

# --- Views (Buttons & Dropdowns) ---

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Store Build Purchase", emoji="🛒", description="Buy a pre-made build"),
            discord.SelectOption(label="Custom Build Order", emoji="🏗️", description="Order a custom build"),
            discord.SelectOption(label="Business/Partnership", emoji="🤝", description="Business inquiries"),
            discord.SelectOption(label="Support/Help", emoji="🛂", description="General support")
        ]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        config = load_config()

        # 1. Validation
        if config["open_category_id"] == 0:
            return await interaction.response.send_message("❌ System not configured. Admin must set categories.", ephemeral=True)

        # Check max tickets
        existing_tickets = 0
        for channel in interaction.guild.channels:
            if isinstance(channel, discord.TextChannel) and channel.topic == str(interaction.user.id):
                existing_tickets += 1

        if existing_tickets >= config["max_tickets_per_user"]:
            return await interaction.response.send_message(f"❌ You have reached the limit of {config['max_tickets_per_user']} open tickets.", ephemeral=True)

        # 2. Update Counter
        config["ticket_counter"] += 1
        save_config(config)
        ticket_id = config["ticket_counter"]

        # 3. Create Channel
        category = interaction.guild.get_channel(config["open_category_id"])
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Add support role perms
        support_role = interaction.guild.get_role(config["support_role_id"])
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel_name = f"ticket-{ticket_id}"
        ticket_channel = await interaction.guild.create_text_channel(
            channel_name, 
            category=category, 
            overwrites=overwrites,
            topic=str(interaction.user.id) # Storing User ID in topic to track ownership
        )

        # 4. Send Welcome Message
        embed = discord.Embed(
            title=f"{self.values[0]}",
            description=f"Hi {interaction.user.mention}!\nYour ticket has been created.\nSupport will be with you shortly.",
            color=0x2b2d31
        )
        embed.set_footer(text="Builder's Heaven Ticket System")

        # Ping support
        msg_content = f"{interaction.user.mention}"
        if support_role:
            msg_content += f" | {support_role.mention}"

        await ticket_channel.send(content=msg_content, embed=embed, view=TicketControls())

        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.blurple, emoji="🔒", custom_id="ticket_lock")
    async def lock(self, interaction: discord.Interaction, button: Button):
        # Lock ticket (User can view but NOT send)
        ticket_owner_id = int(interaction.channel.topic) if interaction.channel.topic and interaction.channel.topic.isdigit() else None
        if ticket_owner_id:
            member = interaction.guild.get_member(ticket_owner_id)
            if member:
                await interaction.channel.set_permissions(member, send_messages=False, read_messages=True)
                await interaction.response.send_message("🔒 **Ticket locked for user.**", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ticket owner not found.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.blurple, emoji="🔓", custom_id="ticket_unlock")
    async def unlock(self, interaction: discord.Interaction, button: Button):
        # Unlock ticket
        ticket_owner_id = int(interaction.channel.topic) if interaction.channel.topic and interaction.channel.topic.isdigit() else None
        if ticket_owner_id:
            member = interaction.guild.get_member(ticket_owner_id)
            if member:
                await interaction.channel.set_permissions(member, send_messages=True, read_messages=True)
                await interaction.response.send_message("🔓 **Ticket unlocked.**", ephemeral=True)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, emoji="✅", custom_id="ticket_claim")
    async def claim(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        if config["claim_category_id"] == 0:
            return await interaction.response.send_message("❌ Claim category not set.", ephemeral=True)

        claim_cat = interaction.guild.get_channel(config["claim_category_id"])

        # Move channel and Rename
        await interaction.channel.edit(category=claim_cat, name=f"claimed-{interaction.channel.name}")

        # Update Embed or Send Message
        embed = discord.Embed(description=f"This ticket has been claimed by {interaction.user.mention}", color=discord.Color.brand_green())
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Ticket claimed.", ephemeral=True)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, emoji="🗑️", custom_id="ticket_delete")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()

    @discord.ui.button(label="Delete & Transcript", style=discord.ButtonStyle.red, emoji="📝", custom_id="ticket_transcript")
    async def transcript(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()

        config = load_config()
        # 1. Fetch History
        messages = [msg async for msg in interaction.channel.history(limit=500)]

        # 2. Generate File
        file_obj = generate_transcript(messages, interaction.channel.name, interaction.user)
        file_discord = discord.File(file_obj, filename=f"transcript-{interaction.channel.name}.html")

        # 3. Send to Log Channel
        if config["transcript_channel_id"] != 0:
            log_channel = interaction.guild.get_channel(config["transcript_channel_id"])
            if log_channel:
                embed = discord.Embed(title="Ticket Closed", color=discord.Color.red())
                embed.add_field(name="Ticket", value=interaction.channel.name)
                embed.add_field(name="Closed By", value=interaction.user.mention)
                await log_channel.send(embed=embed, file=file_discord)

        # 4. DM the User (Ticket Opener)
        ticket_owner_id = int(interaction.channel.topic) if interaction.channel.topic and interaction.channel.topic.isdigit() else None
        if ticket_owner_id:
            member = interaction.guild.get_member(ticket_owner_id)
            if member:
                dm_embed = discord.Embed(
                    title=f"Ticket {interaction.channel.name} Closed",
                    description=f"Your ticket in **{interaction.guild.name}** has been closed.",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Closed by", value=f"{interaction.user} ({interaction.user.id})")
                dm_embed.add_field(name="Time taken", value="N/A") # You can calculate this if you store creation time

                # Reset file pointer for second send
                file_obj.seek(0)
                file_discord_dm = discord.File(file_obj, filename=f"transcript-{interaction.channel.name}.html")

                try:
                    await member.send(embed=dm_embed, file=file_discord_dm)
                except discord.Forbidden:
                    pass # User has DMs off

        await interaction.channel.delete()

# --- The Cog ---
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Re-register views on restart so buttons work
        self.bot.add_view(TicketControls()) 
        # Note: We don't add TicketLauncher() here because that view is usually sent once. 
        # If you want persistent panel buttons, you'd add it here too.

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx):
        """Sends the ticket panel."""
        embed = discord.Embed(
            title="Builder's Heaven",
            description="**Ticket Panel**\n\nPlease create a ticket for any of the following:\n\n• Buying a build or Ordering a custom build\n• Questions about products\n• For business/partnership\n\nChoose the correct option below so we can help you faster.",
            color=0x2b2d31 
        )
        embed.set_image(url="https://media.discordapp.net/attachments/your_image_link_here.png") # Replace with your banner URL if needed
        view = View()
        view.add_item(TicketSelect())
        await ctx.send(embed=embed, view=view)

    # --- Configuration Commands ---

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def tconfig(self, ctx):
        """Shows current setup."""
        config = load_config()
        embed = discord.Embed(title="Ticket Configuration", color=discord.Color.blue())
        embed.add_field(name="Open Category", value=f"<#{config['open_category_id']}>" if config['open_category_id'] else "Not Set")
        embed.add_field(name="Claim Category", value=f"<#{config['claim_category_id']}>" if config['claim_category_id'] else "Not Set")
        embed.add_field(name="Transcript Channel", value=f"<#{config['transcript_channel_id']}>" if config['transcript_channel_id'] else "Not Set")
        embed.add_field(name="Support Role", value=f"<@&{config['support_role_id']}>" if config['support_role_id'] else "Not Set")
        await ctx.send(embed=embed)

    @tconfig.command()
    async def category_open(self, ctx, category: discord.CategoryChannel):
        config = load_config()
        config["open_category_id"] = category.id
        save_config(config)
        await ctx.send(f"✅ Tickets will open in: {category.name}")

    @tconfig.command()
    async def category_claim(self, ctx, category: discord.CategoryChannel):
        config = load_config()
        config["claim_category_id"] = category.id
        save_config(config)
        await ctx.send(f"✅ Claimed tickets will move to: {category.name}")

    @tconfig.command()
    async def logs(self, ctx, channel: discord.TextChannel):
        config = load_config()
        config["transcript_channel_id"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Transcripts will go to: {channel.mention}")

    @tconfig.command()
    async def role(self, ctx, role: discord.Role):
        config = load_config()
        config["support_role_id"] = role.id
        save_config(config)
        await ctx.send(f"✅ Support role set to: {role.name}")

    @tconfig.command()
    async def limit(self, ctx, limit: int):
        config = load_config()
        config["max_tickets_per_user"] = limit
        save_config(config)
        await ctx.send(f"✅ Max tickets per user set to: {limit}")

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))