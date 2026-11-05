"""
Helper Functions Module
Contains utility functions used across the bot
"""

import discord
from core.data_store import data_store

async def send_log(guild_id: str, action: str, author: discord.Member, message: discord.Message):
    """
    Send a log message to the configured logs channel

    Logs important actions like adding/removing stats

    Args:
        guild_id: Discord guild ID
        action: Description of action performed
        author: Member who performed the action
        message: Original message that triggered the action
    """
    logs_channel_id = data_store.guilds.get(guild_id, {}).get('logs_channel')
    if not logs_channel_id:
        return

    try:
        logs_channel = message.guild.get_channel(int(logs_channel_id))
        if not logs_channel:
            return

        # Create message link for easy navigation
        message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

        embed = discord.Embed(
            title="📊 Statistics Log",
            color=discord.Color.green(),
            timestamp=message.created_at
        )

        embed.add_field(name="👤 User", value=author.mention, inline=True)
        embed.add_field(name="⚡ Action", value=action, inline=True)
        embed.add_field(name="📍 Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="🔗 Message Link", value=f"[View Message]({message_link})", inline=False)

        embed.set_thumbnail(url=author.display_avatar.url)
        embed.set_footer(text=f"User ID: {author.id}")

        await logs_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Error sending log: {e}")

def ensure_backward_compatibility(stats: dict) -> dict:
    """
    Ensure older stat entries have all new fields

    When new features are added, this ensures old data works

    Args:
        stats: Player statistics dictionary

    Returns:
        Updated statistics dictionary with all fields
    """
    # Fields that were added later
    if 'best_bowling' not in stats:
        stats['best_bowling'] = 0
    if 'four_fers' not in stats:
        stats['four_fers'] = 0
    if 'catches_taken' not in stats:
        stats['catches_taken'] = 0
    if 'catches_dropped' not in stats:
        stats['catches_dropped'] = 0
    if 'matches' not in stats:
        stats['matches'] = max(stats.get('innings_bat', 0), stats.get('innings_bowl', 0))
    if 'not_outs' not in stats:
        stats['not_outs'] = 0

    return stats
