"""
Statistics Commands Module
Handles viewing, adding, and removing player statistics
"""

import discord
from discord.ext import commands
from typing import Optional
import time

def setup_stats_commands(bot):
    """Setup function to register stats commands"""

    from core.data_store import data_store
    from ui.embeds import create_stats_embed, create_archived_stats_embed
    from utils.parsers import parse_match_stats
    from utils.helpers import send_log

    # View stats command (with tournament support)

    @bot.command(name='stats')
    async def stats(ctx, target: Optional[str] = None, tournament: Optional[str] = None):
        """
        View player statistics (current or archived tournament)

        Usage:
            +stats                  - View your own stats (current)
            +stats @user            - View mentioned user's stats (current)
            +stats @user BOTS19     - View user's archived tournament stats
            +stats BOTS19           - View your archived tournament stats
            +stats username         - View stats by username (current)
            +stats 123456789        - View stats by user ID (current)
        """
        guild_id = str(ctx.guild.id)

        # Determine if tournament parameter is provided
        # If target looks like a tournament name (in the list), treat it as tournament
        tournaments_list = data_store.get_tournament_list(guild_id)

        user_id = None
        tournament_name = None

        # Case 1: +stats (no args) - show own current stats
        if target is None and tournament is None:
            user_id = str(ctx.author.id)
            tournament_name = None

        # Case 2: +stats BOTS19 (target is tournament name) - show own archived stats
        elif target is not None and tournament is None:
            # Check if target is a tournament name
            if target in tournaments_list:
                user_id = str(ctx.author.id)
                tournament_name = target
            # Check if it's a mention
            elif ctx.message.mentions:
                user_id = str(ctx.message.mentions[0].id)
                tournament_name = None
            # Check if it's a user ID
            elif target.isdigit():
                user_id = target
                tournament_name = None
            # Check if it's a username
            else:
                member = discord.utils.find(
                    lambda m: m.name.lower() == target.lower() or
                             m.display_name.lower() == target.lower(),
                    ctx.guild.members
                )
                if member:
                    user_id = str(member.id)
                    tournament_name = None
                else:
                    await ctx.send("❌ User not found!")
                    return

        # Case 3: +stats @user BOTS19 (both provided)
        elif target is not None and tournament is not None:
            if ctx.message.mentions:
                user_id = str(ctx.message.mentions[0].id)
            elif target.isdigit():
                user_id = target
            else:
                member = discord.utils.find(
                    lambda m: m.name.lower() == target.lower() or
                             m.display_name.lower() == target.lower(),
                    ctx.guild.members
                )
                if member:
                    user_id = str(member.id)
                else:
                    await ctx.send("❌ User not found!")
                    return

            tournament_name = tournament

        # Now create the embed based on tournament
        if tournament_name:
            # Check if tournament exists in archive list
            if tournament_name not in tournaments_list:
                # Tournament doesn't exist - just show current stats (ignore invalid name)
                embed = create_stats_embed(user_id, guild_id, ctx.guild)

                from ui.views import StatsView
                view = StatsView(guild_id, user_id, ctx.guild, ctx.author)
                message = await ctx.send(embed=embed, view=view)
                view.message = message
                return

            embed = create_archived_stats_embed(user_id, guild_id, tournament_name, ctx.guild)
            await ctx.send(embed=embed)
        else:
            embed = create_stats_embed(user_id, guild_id, ctx.guild)

            from ui.views import StatsView
            view = StatsView(guild_id, user_id, ctx.guild, ctx.author)
            message = await ctx.send(embed=embed, view=view)
            view.message = message

    # PING COMMAND (Utility)

    @bot.command(name='ping')
    async def ping(ctx):
        """Check bot latency and response time"""
        start_time = time.time()

        message = await ctx.send("⏳ Pinging...")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000
        websocket_latency = bot.latency * 1000

        if websocket_latency < 150:
            status = "Excellent"
            emoji = "✅"
            color = discord.Color.green()
        elif websocket_latency < 300:
            status = "Good"
            emoji = "✅"
            color = discord.Color.green()
        elif websocket_latency < 500:
            status = "Fair"
            emoji = "⚠️"
            color = discord.Color.orange()
        else:
            status = "Poor"
            emoji = "❌"
            color = discord.Color.red()

        embed = discord.Embed(
            title=f"{emoji} **Pong!**",
            description=(
                f"**Response Time:** {response_time:.2f} ms\n"
                f"**Average Latency:** {websocket_latency:.2f} ms\n"
                f"**Status:** {status}"
            ),
            color=color
        )

        timestamp = ctx.message.created_at
        today = discord.utils.utcnow().date()

        if timestamp.date() == today:
            time_str = f"Today at {timestamp.strftime('%I:%M %p')}"
        else:
            time_str = timestamp.strftime('%B %d, %Y at %I:%M %p')

        embed.set_footer(
            text=f"Requested by {ctx.author.name} • {time_str}",
            icon_url=ctx.author.display_avatar.url
        )

        await message.edit(content=None, embed=embed)

    # ADD STATS COMMAND (With Match History)

    @bot.command(name='addstats', aliases=['as'])
    async def add_stats(ctx):
        """
        Add match statistics from raw data (Admin only)

        Usage:
            Reply to a message containing stats in this format:
```python
            user_id, runs, balls_played, runs_conceded, balls_bowled, wickets, not_out
            user_id, runs, balls_played, runs_conceded, balls_bowled, wickets, not_out
```
        """
        guild_id = str(ctx.guild.id)

        # Bot owner bypasses all checks
        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

            # Check if guild is allowed
            data_store.init_guild(guild_id)
            if not data_store.guilds[guild_id]['allowed']:
                await ctx.send("❌ This server doesn't have access to the bot. Contact the bot owner.")
                return

        data_store.init_guild(guild_id)

        # Look for stats in message or reply
        content = ctx.message.content
        if ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            content = ref_msg.content

        stats_list = parse_match_stats(content)

        if not stats_list:
            await ctx.send("❌ No valid statistics found. Please reply to a message with raw match data.")
            return

        data_store.add_stats_with_history(guild_id, stats_list)

        from core.match_history import match_history
        match_number = len(match_history.matches.get(guild_id, []))

        embed = discord.Embed(
            title="✅ Statistics Added",
            description=f"**Match ID: `{match_number}`**\nSuccessfully added stats for {len(stats_list)} players!",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

        await send_log(guild_id, f"Added match stats for {len(stats_list)} players", ctx.author, ctx.message)

    # REMOVE STATS COMMAND (With Recalculation)

    @bot.command(name='removestats', aliases=['rs'])
    async def remove_stats(ctx):
        """
        Remove the LATEST match and recalculate all stats (Admin only)

        Usage:
            +removestats
        """
        from core.match_history import match_history

        guild_id = str(ctx.guild.id)

        # Bot owner bypasses all checks
        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

            # Check if guild is allowed
            data_store.init_guild(guild_id)
            if not data_store.guilds[guild_id]['allowed']:
                await ctx.send("❌ This server doesn't have access to the bot. Contact the bot owner.")
                return

        data_store.init_guild(guild_id)

        latest_match = match_history.get_latest_match(guild_id)

        if not latest_match:
            await ctx.send("❌ No match history found to remove!")
            return

        match_number = len(match_history.matches.get(guild_id, []))
        player_count = len(latest_match['players'])

        removed_match = match_history.remove_latest_match(guild_id)

        if not removed_match:
            await ctx.send("❌ Failed to remove match!")
            return

        # Recalculate stats for all affected players
        recalculated_count = 0
        for player in removed_match['players']:
            user_id = player['user_id']

            # PRESERVE catches before recalculating
            old_stats = data_store.stats[guild_id].get(user_id, {})
            catches_taken = old_stats.get('catches_taken', 0)
            catches_dropped = old_stats.get('catches_dropped', 0)

            # Recalculate batting/bowling from match history
            new_stats = match_history.recalculate_player_stats(guild_id, user_id)

            # RESTORE catches (they're not in match history)
            new_stats['catches_taken'] = catches_taken
            new_stats['catches_dropped'] = catches_dropped

            data_store.stats[guild_id][user_id] = new_stats
            recalculated_count += 1

        data_store.save_data()

        success_embed = discord.Embed(
            title="✅ Statistics Removed",
            description=f"**Match ID: `{match_number}`**\n Successfully removed stats for {player_count} players",
            color=discord.Color.orange()
        )

        await ctx.send(embed=success_embed)

        await send_log(guild_id, f"Removed match #{match_number}", ctx.author, ctx.message)

    # Error handlers (only for non-owners)
    @add_stats.error
    @remove_stats.error
    async def permission_error(ctx, error):
        """Handle permission errors gracefully"""
        # Don't show error for bot owner
        if ctx.author.id == bot.owner_id:
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command!")
