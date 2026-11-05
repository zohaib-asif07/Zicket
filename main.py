"""Entry point: python main.py"""

from config import DISCORD_BOT_TOKEN
from core.bot import bot

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN is missing. Copy .env.example to .env and add your bot token.")
    else:
        print("🚀 Starting Zicket...")
        bot.run(DISCORD_BOT_TOKEN)
