"""
Auto-Catch Detection Module
Handles automatic detection and logging of catch opportunities from cricket bot
"""

import discord
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import CRICKET_BOT_ID, AUTO_CATCH_TIMEOUT
from core.data_store import data_store
from utils.calculations import calculate_catch_percentage

# In-memory storage for pending catch opportunities
# Format: {channel_id: {user_id: str, timestamp: datetime}}
pending_catches: Dict[str, Dict] = {}

def count_mentions(embed: discord.Embed) -> int:
    """
    Count total user mentions in embed description

    Real player catches have 3 mentions:
    - @fielder (first mention)
    - @fielder (second mention)
    - @batter (third mention)

    Bot catches have fewer mentions (0-2)

    Args:
        embed: Discord embed to check

    Returns:
        Number of mentions found
    """
    if not embed.description:
        return 0

    # Find all mentions like <@123456> or <@!123456>
    mentions = re.findall(r'<@!?\d+>', embed.description)
    return len(mentions)

def extract_user_id_from_embed(embed: discord.Embed) -> Optional[str]:
    """
    Extract user ID from embed description (first mention = fielder)

    Looks for mentions like <@123456789> or <@!123456789>

    Args:
        embed: Discord embed to search

    Returns:
        User ID as string, or None if not found
    """
    if not embed.description:
        return None

    # Match Discord mention format (first mention is the fielder)
    match = re.search(r'<@!?(\d+)>', embed.description)
    if match:
        return match.group(1)

    return None

def is_catch_opportunity(message: discord.Message) -> bool:
    """
    Check if message is a catch opportunity from cricket bot

    Args:
        message: Discord message to check

    Returns:
        True if this is a catch opportunity, False otherwise
    """
    # Must be from cricket bot
    if message.author.id != CRICKET_BOT_ID:
        return False

    # Must have embeds
    if not message.embeds:
        return False

    embed = message.embeds[0]

    # Check title for "CHANCE OF WICKET"
    if embed.title and "CHANCE OF WICKET" in embed.title.upper():
        return True

    # Check description for "CHANCE OF WICKET"
    if embed.description and "CHANCE OF WICKET" in embed.description.upper():
        return True

    return False

def is_catch_result(message: discord.Message) -> Optional[str]:
    """
    Check if message contains a catch result from cricket bot

    Args:
        message: Discord message to check

    Returns:
        "taken" if catch was taken
        "dropped" if catch was dropped
        None if not a catch result
    """
    # Must be from cricket bot
    if message.author.id != CRICKET_BOT_ID:
        return None

    content = message.content.upper()

    if "TOOK THE CATCH" in content:
        return "taken"

    if "BOZO DROPPED" in content or "DROPPED THE CATCH" in content:
        return "dropped"

    return None

async def handle_catch_opportunity(message: discord.Message, bot) -> None:
    """
    Handle detection of catch opportunity

    Only processes if exactly 3 mentions (real player)
    Skips and notifies if bot is fielding (0-2 mentions)

    Args:
        message: The catch opportunity message from cricket bot
        bot: Bot instance for sending messages
    """
    channel_id = str(message.channel.id)
    guild_id = str(message.guild.id)

    embed = message.embeds[0]

    # Count mentions to detect if fielder is a bot
    mention_count = count_mentions(embed)

    # Only proceed if exactly 3 mentions (real player catch)
    if mention_count != 3:
        # Send bot detection embed (only if auto-catch is enabled)
        if data_store.is_auto_catch_enabled(guild_id, channel_id):
            bot_embed = discord.Embed(
                title="🤖 Bot Detected in Catch",
                description=(
                    "A bot was detected in this catch opportunity.\n"
                    "Automatic logging has been skipped.\n\n"
                    "**To log this catch manually:**\n"
                    "`+logcatch @user`"
                ),
                color=discord.Color.orange()
            )
            bot_embed.set_footer(text=f"Mentions detected: {mention_count} (Expected: 3)")
            await message.channel.send(embed=bot_embed)
        return  # Skip auto-logging

    # Extract user ID (first mention = fielder)
    user_id = extract_user_id_from_embed(embed)
    if not user_id:
        return

    pending_catches[channel_id] = {
        "user_id": user_id,
        "timestamp": datetime.now()
    }

    member = message.guild.get_member(int(user_id))
    if not member:
        return

    stats = data_store.stats.get(guild_id, {}).get(user_id)

    catch_embed = discord.Embed(
        title="🏏 CATCH OPPORTUNITY DETECTED!",
        description=f"A catch is coming towards {member.mention}!",
        color=discord.Color.blue()
    )

    # Add fielding record if user has stats
    if stats:
        catches_taken = stats.get('catches_taken', 0)
        catches_dropped = stats.get('catches_dropped', 0)
        total = catches_taken + catches_dropped

        if total > 0:
            catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)

            catch_embed.add_field(
                name="🧤 Fielding Record",
                value=f"✅ Caught: {catches_taken} | ❌ Dropped: {catches_dropped} | 📊 Success: {catch_percentage}%",
                inline=False
            )
        else:
            catch_embed.add_field(
                name="🧤 Fielding Record",
                value="First catch opportunity!",
                inline=False
            )
    else:
        catch_embed.add_field(
            name="🧤 Fielding Record",
            value="First catch opportunity!",
            inline=False
        )

    catch_embed.set_thumbnail(url=member.display_avatar.url)

    await message.channel.send(embed=catch_embed)

async def handle_catch_result(message: discord.Message, result: str, bot) -> None:
    """
    Handle detection of catch result

    Matches with pending catch and updates stats automatically

    Args:
        message: The catch result message from cricket bot
        result: "taken" or "dropped"
        bot: Bot instance for sending messages
    """
    channel_id = str(message.channel.id)
    guild_id = str(message.guild.id)

    # Check if there's a pending catch in this channel
    if channel_id not in pending_catches:
        return

    pending = pending_catches[channel_id]

    # Check if catch opportunity is still valid (within timeout)
    time_diff = datetime.now() - pending["timestamp"]
    if time_diff > timedelta(seconds=AUTO_CATCH_TIMEOUT):
        # Timeout - remove pending catch
        del pending_catches[channel_id]
        return

    user_id = pending["user_id"]

    caught = (result == "taken")
    data_store.add_catch(guild_id, user_id, caught)

    stats = data_store.stats.get(guild_id, {}).get(user_id, {})
    catches_taken = stats.get('catches_taken', 0)
    catches_dropped = stats.get('catches_dropped', 0)
    catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)

    member = message.guild.get_member(int(user_id))
    username = member.name if member else f"User {user_id}"

    if caught:
        result_embed = discord.Embed(
            title="✅ CATCH TAKEN!",
            description=f"**{username}** took the catch!\n\n🧤 **Total Catches:** {catches_taken}\n📊 **Success Rate:** {catch_percentage}%",
            color=discord.Color.green()
        )
    else:
        result_embed = discord.Embed(
            title="❌ CATCH DROPPED!",
            description=f"**{username}** dropped the catch!\n\n💔 **Total Drops:** {catches_dropped}\n📊 **Success Rate:** {catch_percentage}%",
            color=discord.Color.red()
        )

    if member:
        result_embed.set_thumbnail(url=member.display_avatar.url)

    await message.channel.send(embed=result_embed)

    del pending_catches[channel_id]

async def process_cricket_bot_message(message: discord.Message, bot) -> None:
    """
    Main entry point for processing cricket bot messages

    Checks if auto-catch is enabled and processes accordingly

    Args:
        message: Discord message to process
        bot: Bot instance
    """
    guild_id = str(message.guild.id)
    channel_id = str(message.channel.id)

    # Check if auto-catch is enabled for this server AND channel
    if not data_store.is_auto_catch_enabled(guild_id, channel_id):
        return

    if is_catch_opportunity(message):
        await handle_catch_opportunity(message, bot)
        return

    result = is_catch_result(message)
    if result:
        await handle_catch_result(message, result, bot)
        return
