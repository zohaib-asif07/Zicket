"""
Power Surge Feature Module
Handles power surge activation and monitoring for HandCricket matches
"""

import discord
from discord.ui import View, Button
from datetime import datetime

from config import CRICKET_BOT_ID, CAPTAIN_ROLE_ID, VICE_CAPTAIN_ROLE_ID

POWERSURGE_TIMEOUT = 300  # 5 minutes in seconds

# Global power surge tracking
# Format: {guild_id: {channel_id: {'active': bool, 'confirmed': bool, 'bowler_id': str, 'timestamp': datetime}}}
power_surge_states = {}

# EMBEDS

def create_confirmation_embed() -> discord.Embed:
    """Create power surge confirmation embed"""
    embed = discord.Embed(
        title="⚡ Power Surge Activation",
        description=(
            "Are you sure you want to enable **Power Surge** in the next over?\n\n"
            "**Note:** You can only use Power Surge once per innings."
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Choose wisely! This cannot be undone.")
    return embed

def create_pending_embed() -> discord.Embed:
    """Create pending power surge embed"""
    embed = discord.Embed(
        title="⚡ Power Surge Activated!",
        description=(
            "**Power Surge will be enabled in the next over.**\n\n"
            "Waiting for the current over to end..."
        ),
        color=discord.Color.orange()
    )
    embed.set_footer(text="⏳ Monitoring for next over...")
    return embed

def create_enabled_embed(bowler: discord.Member, batters: list, guild: discord.Guild) -> discord.Embed:
    """Create power surge enabled embed - SIMPLE VERSION with pings"""
    batter_mentions = []
    if batters:
        for batter_name in batters:
            # Try to find member by username
            member = discord.utils.find(
                lambda m: m.name.lower() == batter_name.lower() or
                         m.display_name.lower() == batter_name.lower(),
                guild.members
            )
            if member:
                batter_mentions.append(member.mention)
            else:
                # Fallback to text if member not found
                batter_mentions.append(f"**{batter_name}**")

    if batter_mentions:
        batter_text = " and ".join(batter_mentions)
    else:
        batter_text = "**Batters**"

    embed = discord.Embed(
        title="⚡ POWER SURGE ENABLED! ⚡",
        description=(
            f"{bowler.mention} - The Power Surge is now active!\n"
            f"🎯 You can only bowl **6** twice in this over. Use them wisely!\n\n"
            f"{batter_text}\n"
            f"🏏 Opponent bowler can use **6** only twice!"
        ),
        color=discord.Color.red()
    )

    embed.set_footer(text="⚠️ Rule violation = FREE WIN for opponent team")
    return embed

def create_new_batter_embed(batter: discord.Member) -> discord.Embed:
    """Create embed for new batter during power surge"""
    embed = discord.Embed(
        title="⚡ Power Surge Still Active!",
        description=(
            f"{batter.mention}\n\n"
            f"🏏 **Power Surge is enabled!**\n"
            f"The bowler can only use **6** twice in this over.\n\n"
            f"Make the most of this opportunity!"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="⚡ Power Surge continues...")
    return embed

def create_disabled_embed() -> discord.Embed:
    """Create power surge disabled embed"""
    embed = discord.Embed(
        title="⚡ Power Surge Disabled",
        description=(
            "**Power Surge has ended!**\n\n"
            "🎳 The bowler can now use all numbers freely.\n"
            "Thanks for playing fair! 🏏"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="⚡ Power Surge Over")
    return embed

def create_allout_embed() -> discord.Embed:
    """Create all out before power surge embed"""
    embed = discord.Embed(
        title="😅 Oops! Team All Out!",
        description=(
            "The team got all out before using Power Surge! 😢\n\n"
            "**Pro Tip:** Try to use Power Surge wisely during the innings next time."
        ),
        color=discord.Color.orange()
    )
    embed.set_footer(text="Better luck next time! 🏏")
    return embed

def create_innings_ended_embed() -> discord.Embed:
    """Create innings ended embed"""
    embed = discord.Embed(
        title="🏁 Innings Ended!",
        description="**Power Surge is now disabled.**\n\nThe innings has concluded.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="⚡ Power Surge Over")
    return embed

def create_cancelled_embed() -> discord.Embed:
    """Create cancelled power surge embed"""
    embed = discord.Embed(
        title="❌ Power Surge Cancelled",
        description="Power Surge activation was cancelled.",
        color=discord.Color.red()
    )
    return embed

# Confirmation view

class PowerSurgeConfirmView(View):
    """View for power surge confirmation buttons"""

    def __init__(self, guild_id: str, channel_id: str, author: discord.Member):
        super().__init__(timeout=30)
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.author = author
        self.confirmed = False

    @discord.ui.button(label="Yes, Enable Power Surge", style=discord.ButtonStyle.success, emoji="⚡")
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        """Confirm power surge activation"""
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the captain can confirm this!", ephemeral=True)
            return

        self.confirmed = True

        if self.guild_id not in power_surge_states:
            power_surge_states[self.guild_id] = {}

        power_surge_states[self.guild_id][self.channel_id] = {
            'active': False,  # Not active yet, waiting for next over
            'confirmed': True,
            'bowler_id': None,
            'timestamp': datetime.now()
        }

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=create_pending_embed())

    @discord.ui.button(label="No, Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Cancel power surge activation"""
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the captain can cancel this!", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=create_cancelled_embed())

    async def on_timeout(self):
        """Handle timeout"""
        for item in self.children:
            item.disabled = True

# Helper functions

def extract_bowler_mention(embed: discord.Embed) -> str:
    """Extract bowler mention from 'After this over' embed"""
    import re

    # Check fields (the embed uses fields)
    if embed.fields:
        for field in embed.fields:
            if "next bowler" in field.name.lower():
                # Find mention in value
                mention_pattern = r'<@!?(\d+)>'
                matches = re.findall(mention_pattern, field.value)

                if matches:
                    return matches[0]

    return None

def extract_batter_names(embed: discord.Embed) -> list:
    """Extract batter usernames from 'After this over' embed"""
    batters = []

    # Fields contain the scores
    if embed.fields:
        for field in embed.fields:
            # Look for fields with "'s score" in the name
            if "'s score" in field.name:
                username = field.name.replace("'s score", "").strip()
                if username and username != 'Partnership':
                    batters.append(username)

    return batters

def extract_batter_mention(embed: discord.Embed) -> str:
    """
    Extract new batter from 'Batter out!' embed

    Returns:
        - User ID string if new batter is mentioned
        - "NO_MENTION_BUT_EXISTS" if new batter exists but not mentioned (like Bot)
        - None if no "Next batsman" field (= innings ended)
    """
    import re

    if embed.fields:
        for field in embed.fields:
            if "next batsman" in field.name.lower():
                # Check if there's a mention in the value
                mention_pattern = r'<@!?(\d+)>'
                matches = re.findall(mention_pattern, field.value)

                if matches:
                    return matches[0]
                elif field.value.strip():
                    # Field exists with text (like **Bot2**) but no mention
                    return "NO_MENTION_BUT_EXISTS"

    # No "Next batsman" field = innings ended / all out
    return None

def is_power_surge_pending(guild_id: str, channel_id: str) -> bool:
    """Check if power surge is pending in channel"""
    if guild_id not in power_surge_states:
        return False
    if channel_id not in power_surge_states[guild_id]:
        return False

    state = power_surge_states[guild_id][channel_id]

    # Check if confirmed but not active yet
    if state['confirmed'] and not state['active']:
        # Check if not expired (5 minutes)
        time_diff = datetime.now() - state['timestamp']
        if time_diff.total_seconds() <= POWERSURGE_TIMEOUT:
            return True
        else:
            # Expired, remove state
            del power_surge_states[guild_id][channel_id]
            return False

    return False

def is_power_surge_active(guild_id: str, channel_id: str) -> bool:
    """Check if power surge is currently active"""
    if guild_id not in power_surge_states:
        return False
    if channel_id not in power_surge_states[guild_id]:
        return False

    return power_surge_states[guild_id][channel_id].get('active', False)

def activate_power_surge(guild_id: str, channel_id: str, bowler_id: str):
    """Activate power surge"""
    if guild_id not in power_surge_states:
        power_surge_states[guild_id] = {}

    if channel_id in power_surge_states[guild_id]:
        power_surge_states[guild_id][channel_id]['active'] = True
        power_surge_states[guild_id][channel_id]['bowler_id'] = bowler_id

def deactivate_power_surge(guild_id: str, channel_id: str):
    """Deactivate power surge"""
    if guild_id in power_surge_states:
        if channel_id in power_surge_states[guild_id]:
            del power_surge_states[guild_id][channel_id]

# Message processor

async def process_cricket_bot_message(message: discord.Message):
    """Process messages from cricket bot for power surge monitoring"""
    guild_id = str(message.guild.id)
    channel_id = str(message.channel.id)

    # Must be from cricket bot with embed
    if message.author.id != CRICKET_BOT_ID:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    # SCENARIO 1: Batter Out (while pending OR active)
    if embed.title and embed.title.strip() == "Batter out!":
        # Check if there's a new batter field
        new_batter_result = extract_batter_mention(embed)

        # If power surge is PENDING and no new batter = team got all out before activation
        if is_power_surge_pending(guild_id, channel_id):
            if not new_batter_result:
                # No next batsman = team got all out!
                deactivate_power_surge(guild_id, channel_id)
                await message.channel.send(embed=create_allout_embed())
                return
            # Otherwise, just wait for "After this over" to activate

        # If power surge is ACTIVE
        if is_power_surge_active(guild_id, channel_id):
            if new_batter_result == "NO_MENTION_BUT_EXISTS":
                return
            elif new_batter_result:
                new_batter = message.guild.get_member(int(new_batter_result))
                if new_batter:
                    # Ping outside embed for notification
                    await message.channel.send(
                        content=new_batter.mention,
                        embed=create_new_batter_embed(new_batter)
                    )
                return
            else:
                # No new batter field = last wicket, innings ended
                deactivate_power_surge(guild_id, channel_id)
                await message.channel.send(embed=create_innings_ended_embed())
                return

    # SCENARIO 2: After This Over (activate power surge)
    if embed.title and embed.title.strip() == "After this over":
        if is_power_surge_pending(guild_id, channel_id):
            # Extract bowler mention (LAST mention in description)
            bowler_id = extract_bowler_mention(embed)

            if bowler_id:
                bowler = message.guild.get_member(int(bowler_id))

                # Extract batter names
                batter_names = extract_batter_names(embed)

                # Activate power surge
                activate_power_surge(guild_id, channel_id, bowler_id)

                batter_mentions = []
                if batter_names:
                    for batter_name in batter_names:
                        # Try to find member by username
                        member = discord.utils.find(
                            lambda m: m.name.lower() == batter_name.lower() or
                                     m.display_name.lower() == batter_name.lower(),
                            message.guild.members
                        )
                        if member:
                            batter_mentions.append(member.mention)

                # Create ping message outside embed (notifications work here!)
                ping_text = f"{bowler.mention}"
                if batter_mentions:
                    ping_text += f", {', '.join(batter_mentions)}"

                await message.channel.send(
                    content=ping_text,
                    embed=create_enabled_embed(bowler, batter_names, message.guild)
                )
                return

        # If power surge is already active, disable it (next over ends power surge)
        if is_power_surge_active(guild_id, channel_id):
            deactivate_power_surge(guild_id, channel_id)
            await message.channel.send(embed=create_disabled_embed())
            return

    # Note: We removed the separate "Batter Out during active" scenario
    # since it's now handled in SCENARIO 1 which covers both pending and active states

# Setup function

def setup_powersurge_commands(bot):
    """Setup function to register power surge commands"""

    @bot.command(name='powersurge', aliases=['ps'])
    async def power_surge(ctx):
        """
        Activate Power Surge for the next over (Captain only)

        Power Surge limits the bowler to using '6' only twice in an over.
        Can only be used once per innings.

        Usage:
            +powersurge
            +ps
        """
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        # Check permissions: Captain role or bot owner
        has_captain_role = False
        has_vice_captain_role = False

        if ctx.guild.get_role(CAPTAIN_ROLE_ID) in ctx.author.roles:
            has_captain_role = True
        if ctx.guild.get_role(VICE_CAPTAIN_ROLE_ID) in ctx.author.roles:
            has_vice_captain_role = True

        if ctx.author.id != bot.owner_id and not has_captain_role and not has_vice_captain_role:
            await ctx.send("❌ **Only team captains or vice captains can activate Power Surge!** ❌\n\nFocus on your own performance 🤬 Let the Captain & VC do their job!!! ***Zyada ungli nah kro*** ")
            return

        # Check if power surge is already pending or active
        if is_power_surge_pending(guild_id, channel_id):
            await ctx.send("⚠️ Power Surge is already pending for this channel!")
            return

        if is_power_surge_active(guild_id, channel_id):
            await ctx.send("⚠️ Power Surge is already active in this channel!")
            return

        embed = create_confirmation_embed()
        view = PowerSurgeConfirmView(guild_id, channel_id, ctx.author)
        await ctx.send(embed=embed, view=view)

    @bot.command(name='pshelp')
    async def help_powersurge(ctx):
        """
        Show help for Power Surge feature

        Usage:
            +pshelp
        """
        embed = discord.Embed(
            title="⚡ POWER SURGE - HELP GUIDE",
            description=(
                "When power surge is enabled, bowler can do **6 only twice** in an over.\n"
            ),
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📝 USAGE",
            value=(
                "**Command:** `+powersurge` or `+ps` ─ ୨୧ ─ `+psdisable`\n"
                "**Who can use:** Only team captains can use it.\n"
                "**Limit:** Once per innings"
            ),
            inline=False
        )


        embed.add_field(
            name="⛔ WARNING",
            value=(
                "• Bowler can bowl **6** only **twice** in that over\n"
                "• **Breaking the rule = **FREE WIN** for opponent**\n"
            ),
            inline=False
        )

        embed.set_footer(text="🚫 Once per innings • Bowler can do 6 only twice")

        await ctx.send(embed=embed)
    @bot.command(name='psdisable')
    async def disable_power_surge(ctx):
        """
        Disable/Cancel Power Surge (Admin or Owner only)

        Can cancel both pending and active Power Surge

        Usage:
            +psdisable
        """
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        # Check permissions: Admin or bot owner
        if ctx.author.id != bot.owner_id and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Only administrators can disable Power Surge!")
            return

        # Check if power surge is pending or active
        is_pending = is_power_surge_pending(guild_id, channel_id)
        is_active = is_power_surge_active(guild_id, channel_id)

        if not is_pending and not is_active:
            await ctx.send("⚠️ No Power Surge is currently active or pending in this channel!")
            return

        # Deactivate power surge
        deactivate_power_surge(guild_id, channel_id)

        status = "pending" if is_pending else "active"
        embed = discord.Embed(
            title="❌ Power Surge Cancelled",
            description=f"Power Surge ({status}) has been manually disabled by {ctx.author.mention}.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Power Surge can be activated again using +ps")

        await ctx.send(embed=embed)

    @bot.listen('on_message')
    async def on_message_powersurge(message):
        """Listen for cricket bot messages"""
        if message.author.bot and message.author.id == CRICKET_BOT_ID:
            await process_cricket_bot_message(message)
