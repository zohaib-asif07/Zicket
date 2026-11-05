"""Bot settings and constants. Server-specific IDs are read from the .env file."""

import os

import discord
from dotenv import load_dotenv

load_dotenv()


def _env_int(name, default=0):
    value = os.getenv(name, "").strip()
    return int(value) if value.isdigit() else default


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Your Discord user ID; unlocks owner-only commands.
OWNER_ID = _env_int("OWNER_ID")

# The HandCricket bot whose messages are read for auto-catch, wickets and power surge.
CRICKET_BOT_ID = _env_int("CRICKET_BOT_ID", 753191385296928808)

# Roles allowed to activate Power Surge.
CAPTAIN_ROLE_ID = _env_int("CAPTAIN_ROLE_ID")
VICE_CAPTAIN_ROLE_ID = _env_int("VICE_CAPTAIN_ROLE_ID")

DEFAULT_PREFIX = "+"
DEFAULT_TOURNAMENT = "6PSL S1"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

LEADERBOARD_PER_PAGE = 9

# Minimum activity before a player shows up in certain leaderboards.
MIN_CATCH_OPPORTUNITIES = 1
MIN_BALLS_FOR_STRIKE_RATE = 1

MAX_RATING = 99

# Timeouts, in seconds.
CATCH_BUTTON_TIMEOUT = 300
COMMAND_RESPONSE_TIMEOUT = 60
AUTO_CATCH_TIMEOUT = 40  # window for matching a catch chance to its result
