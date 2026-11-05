"""
Bot Core Module
Contains the main Bot class and event handlers
"""

import discord
from discord.ext import commands
from config import intents, OWNER_ID, DEFAULT_PREFIX
from core.data_store import data_store

class Bot(commands.Bot):
    """
    Main bot class with custom prefix handling
    """

    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None  # We use custom help command
        )
        self.owner_id = OWNER_ID

    async def get_prefix(self, message):
        """
        Dynamic prefix system - each guild can have its own prefix

        Args:
            message: Discord message object

        Returns:
            The prefix for the guild (or default if DM)
        """
        if not message.guild:
            return DEFAULT_PREFIX

        guild_id = str(message.guild.id)
        data_store.init_guild(guild_id)
        return data_store.guilds[guild_id]['prefix']

bot = Bot()

@bot.event
async def on_ready():
    """Event handler for when bot successfully connects to Discord"""
    print(f'✅ {bot.user} is ready and online!')
    print(f'📊 Serving {len(bot.guilds)} guilds')
    print(f'👑 Owner ID: {bot.owner_id}')
    print('🏏 Wicket graphics enabled')
    print('⚡ Power Surge feature enabled')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━')


@bot.event
async def on_message(message):
    """
    Event handler for all messages

    Processes:
    1. Auto-catch detection
    2. Wicket graphics generation
    3. Power Surge monitoring
    4. Commands
    """
    # Ignore DMs
    if not message.guild:
        return

    # Don't process messages from the bot itself
    if message.author == bot.user:
        return

    # Import here to avoid circular imports
    from utils.auto_catch import process_cricket_bot_message
    from utils.wicket_graphics import process_batter_out_message

    await process_cricket_bot_message(message, bot)

    await process_batter_out_message(message, bot)

    # MAINTENANCE MODE CHECK (before processing commands)
    if data_store.is_maintenance_mode() and message.author.id != bot.owner_id:
        # Check if message starts with bot prefix
        prefix = await bot.get_prefix(message)
        if message.content.startswith(prefix):
            maintenance_embed = discord.Embed(
                title="🚧 Bot Under Maintenance",
                description=(
                    "We are currently updating the bot.\n"
                    "**All commands are temporarily disabled.**\n"
                ),
                color=discord.Color.orange()
            )
            maintenance_embed.set_footer(text="Maintenance in progress • Thank you for your patience")
            await message.channel.send(embed=maintenance_embed)
            return  # Don't process commands

    await bot.process_commands(message)

# Import and setup commands after bot is created to avoid circular imports
from commands.stats import setup_stats_commands
from commands.leaderboard import setup_leaderboard_commands
from commands.fielding import setup_fielding_commands
from commands.admin import setup_admin_commands
from commands.owner import setup_owner_commands
from commands.auto_catch_toggle import setup_auto_catch_toggle
from commands.wicket import setup_wicket_commands
from commands.points_table import setup_points_table_commands
from commands.team_management import setup_team_management_commands
from commands.powersurge import setup_powersurge_commands
from commands.all_time import setup_all_time_commands

setup_stats_commands(bot)
setup_leaderboard_commands(bot)
setup_fielding_commands(bot)
setup_admin_commands(bot)
setup_owner_commands(bot)
setup_auto_catch_toggle(bot)
setup_wicket_commands(bot)
setup_points_table_commands(bot)
setup_team_management_commands(bot)
setup_powersurge_commands(bot)
setup_all_time_commands(bot)
