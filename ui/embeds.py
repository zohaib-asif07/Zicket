"""
Discord Embeds Module
Contains all embed creation functions for displaying statistics
"""

import discord
from typing import Dict
from core.data_store import data_store

# Combined calculations from both parts
from utils.calculations import (
    calculate_average, calculate_strike_rate, calculate_bowling_avg,
    calculate_economy, calculate_batting_rating, calculate_bowling_rating,
    calculate_overall_rating, get_role_emoji, calculate_fantasy,
    calculate_catch_percentage, get_fielding_grade
)

from utils.helpers import ensure_backward_compatibility
from config import MIN_CATCH_OPPORTUNITIES, MIN_BALLS_FOR_STRIKE_RATE

# Player statistics embeds (current)

def create_stats_embed(user_id: str, guild_id: str, guild: discord.Guild) -> discord.Embed:
    """
    Create comprehensive player statistics embed (CURRENT TOURNAMENT)

    Args:
        user_id: Discord user ID
        guild_id: Discord guild ID
        guild: Discord guild object

    Returns:
        Discord embed with player statistics
    """
    stats = data_store.stats.get(guild_id, {}).get(user_id)

    if not stats:
        embed = discord.Embed(
            title="No Stats Found",
            description="This player has no recorded statistics.",
            color=discord.Color.red()
        )
        return embed

    member = guild.get_member(int(user_id))
    username = member.name if member else f"User {user_id}"

    # Ensure backward compatibility
    stats = ensure_backward_compatibility(stats)

    bat_avg = calculate_average(stats['runs'], stats['dismissals'])
    strike_rate = calculate_strike_rate(stats['runs'], stats['balls_played'])
    bowl_avg = calculate_bowling_avg(stats['runs_conceded'], stats['wickets'])
    economy = calculate_economy(stats['runs_conceded'], stats['balls_bowled'])

    bat_rating = calculate_batting_rating(stats)
    bowl_rating = calculate_bowling_rating(stats)
    overall_rating = calculate_overall_rating(bat_rating, bowl_rating)
    fantasy = calculate_fantasy(stats, bat_rating, bowl_rating)

    role_name, role_emoji = get_role_emoji(bat_rating, bowl_rating)

    tournament = data_store.guilds.get(guild_id, {}).get('tournament', '6PSL S1')
    total_matches = stats.get('matches', max(stats['innings_bat'], stats['innings_bowl']))

    embed = discord.Embed(
        title=f"{username}'s Hand Cricket Stats",
        description=f"{tournament} | Matches: {total_matches} | Fantasy: {fantasy}\n{role_name} {role_emoji} {overall_rating} | Bat: {bat_rating} | Bowl: {bowl_rating}",
        color=discord.Color.blue()
    )

    if member:
        embed.set_thumbnail(url=member.display_avatar.url)

    # Batting statistics

    # Show * if player has not outs and never been dismissed
    avg_display = f"{bat_avg}*" if stats['dismissals'] == 0 and stats['innings_bat'] > 0 else str(bat_avg)

    batting = (
        f"🏏 **Innings:** {stats['innings_bat']}\n"
        f"💥 **Runs:** {stats['runs']}\n"
        f"⚾ **Balls:** {stats['balls_played']}\n"
        f"📊 **Avg:** {avg_display}\n"
        f"⚡ **SR:** {strike_rate}\n"
        f"🌟 **50s:** {stats['fifties']}\n"
        f"💯 **100s:** {stats['hundreds']}\n"
        f"🦆 **Ducks:** {stats['ducks']}\n"
        f"🏆 **High Score:** {stats['high_score']}"
    )

    # Bowling statistics
    bowling = (
        f"🎳 **Innings:** {stats['innings_bowl']}\n"
        f"🎯 **Wickets:** {stats['wickets']}\n"
        f"⚾ **Balls:** {stats['balls_bowled']}\n"
        f"📊 **Avg:** {bowl_avg}\n"
        f"💰 **Eco:** {economy}\n"
        f"🥉 **3w:** {stats['three_fers']}\n"
        f"🥇 **4w:** {stats['four_fers']}\n"
        f"🏃 **Runs Conceded:** {stats['runs_conceded']}\n"
        f"🌟 **Best:** {stats['best_bowling']}"
    )

    embed.add_field(name="Batting", value=batting, inline=True)
    embed.add_field(name="Bowling", value=bowling, inline=True)

    # FIELDING STATISTICS (if any)
    catches_taken = stats.get('catches_taken', 0)
    catches_dropped = stats.get('catches_dropped', 0)

    if catches_taken > 0 or catches_dropped > 0:
        catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)
        embed.add_field(
            name="Fielding",
            value=f"🧤 **Caught:** {catches_taken} | 🚫 **Dropped:** {catches_dropped} | 📊 **Success:** {catch_percentage}%",
            inline=False
        )

    return embed

# Player statistics embeds (archived)

def create_archived_stats_embed(user_id: str, guild_id: str, tournament_name: str, guild: discord.Guild) -> discord.Embed:
    """
    Create comprehensive player statistics embed (ARCHIVED TOURNAMENT)

    Args:
        user_id: Discord user ID
        guild_id: Discord guild ID
        tournament_name: Name of archived tournament
        guild: Discord guild object

    Returns:
        Discord embed with archived player statistics
    """
    archived_stats = data_store.load_tournament_stats(guild_id, tournament_name)
    stats = archived_stats.get(user_id)

    if not stats:
        embed = discord.Embed(
            title="No Stats Found",
            description=f"This player has no recorded statistics in **{tournament_name}**.",
            color=discord.Color.red()
        )
        return embed

    member = guild.get_member(int(user_id))
    username = member.name if member else f"User {user_id}"

    # Ensure backward compatibility
    stats = ensure_backward_compatibility(stats)

    bat_avg = calculate_average(stats['runs'], stats['dismissals'])
    strike_rate = calculate_strike_rate(stats['runs'], stats['balls_played'])
    bowl_avg = calculate_bowling_avg(stats['runs_conceded'], stats['wickets'])
    economy = calculate_economy(stats['runs_conceded'], stats['balls_bowled'])

    bat_rating = calculate_batting_rating(stats)
    bowl_rating = calculate_bowling_rating(stats)
    overall_rating = calculate_overall_rating(bat_rating, bowl_rating)
    fantasy = calculate_fantasy(stats, bat_rating, bowl_rating)

    role_name, role_emoji = get_role_emoji(bat_rating, bowl_rating)

    # Use new matches field
    total_matches = stats.get('matches', max(stats['innings_bat'], stats['innings_bowl']))

    # Create main embed with ARCHIVE indicator
    embed = discord.Embed(
        title=f"{username}'s Hand Cricket Stats",
        description=f"**{tournament_name}** | Matches: {total_matches} | Fantasy: {fantasy}\n{role_name} {role_emoji} {overall_rating} | Bat: {bat_rating} | Bowl: {bowl_rating}",
        color=discord.Color.gold()
    )

    if member:
        embed.set_thumbnail(url=member.display_avatar.url)

    # Batting statistics

    # Show * if player has not outs and never been dismissed
    avg_display = f"{bat_avg}*" if stats['dismissals'] == 0 and stats['innings_bat'] > 0 else str(bat_avg)

    batting = (
        f"🏏 **Innings:** {stats['innings_bat']}\n"
        f"💥 **Runs:** {stats['runs']}\n"
        f"⚾ **Balls:** {stats['balls_played']}\n"
        f"📊 **Avg:** {avg_display}\n"
        f"⚡ **SR:** {strike_rate}\n"
        f"🌟 **50s:** {stats['fifties']}\n"
        f"💯 **100s:** {stats['hundreds']}\n"
        f"🦆 **Ducks:** {stats['ducks']}\n"
        f"🏆 **High Score:** {stats['high_score']}"
    )

    # Bowling statistics
    bowling = (
        f"🎳 **Innings:** {stats['innings_bowl']}\n"
        f"🎯 **Wickets:** {stats['wickets']}\n"
        f"⚾ **Balls:** {stats['balls_bowled']}\n"
        f"📊 **Avg:** {bowl_avg}\n"
        f"💰 **Eco:** {economy}\n"
        f"🥉 **3w:** {stats['three_fers']}\n"
        f"🥇 **4w:** {stats['four_fers']}\n"
        f"🏃 **Runs Conceded:** {stats['runs_conceded']}\n"
        f"🌟 **Best:** {stats['best_bowling']}"
    )

    embed.add_field(name="Batting", value=batting, inline=True)
    embed.add_field(name="Bowling", value=bowling, inline=True)

    # FIELDING STATISTICS (if any)
    catches_taken = stats.get('catches_taken', 0)
    catches_dropped = stats.get('catches_dropped', 0)

    if catches_taken > 0 or catches_dropped > 0:
        catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)
        embed.add_field(
            name="Fielding",
            value=f"🧤 **Caught:** {catches_taken} | 🚫 **Dropped:** {catches_dropped} | 📊 **Success:** {catch_percentage}%",
            inline=False
        )

    embed.set_footer(text="📜 This is archived data and cannot be modified")

    return embed

# Fielding statistics embeds

def create_catch_stats_embed(user_id: str, guild_id: str, guild: discord.Guild) -> discord.Embed:
    """
    Create detailed fielding statistics embed

    Args:
        user_id: Discord user ID
        guild_id: Discord guild ID
        guild: Discord guild object

    Returns:
        Discord embed with fielding statistics
    """
    stats = data_store.stats.get(guild_id, {}).get(user_id)

    if not stats:
        embed = discord.Embed(
            title="No Stats Found",
            description="This player has no recorded statistics.",
            color=discord.Color.red()
        )
        return embed

    member = guild.get_member(int(user_id))
    username = member.name if member else f"User {user_id}"

    # Ensure backward compatibility
    stats = ensure_backward_compatibility(stats)

    catches_taken = stats['catches_taken']
    catches_dropped = stats['catches_dropped']
    total_opportunities = catches_taken + catches_dropped
    catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)


    # No data case
    if total_opportunities == 0:
        embed = discord.Embed(
            title=f"🧤 {username}'s Fielding Stats",
            description="***No fielding data recorded yet!***",
            color=discord.Color.light_gray()
        )

        if member:
            embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="🏏 Ready to Field?",
            value=(
                "This player hasn't faced any catch opportunities yet.\n"
                "When they do, their stats will appear here!\n\n"
                "**What gets tracked:**\n"
                "• Catches taken ✅\n"
                "• Catches dropped ❌\n"
                "• Success rate 📊\n"
                "• Server rankings 🏆"
            ),
            inline=False
        )

        embed.set_footer(text="Get ready to catch them all! 🧤")
        return embed

    # Has data case
    grade_name, grade_emoji = get_fielding_grade(catch_percentage)

    # Color based on performance
    if catch_percentage >= 75:
        color = discord.Color.green()
    elif catch_percentage >= 50:
        color = discord.Color.orange()
    else:
        color = discord.Color.red()

    embed = discord.Embed(
        title=f"🧤 {username}'s Fielding Stats",
        description=f"{grade_emoji} **{grade_name}** {grade_emoji}",
        color=color
    )

    if member:
        embed.set_thumbnail(url=member.display_avatar.url)

    # Main statistics
    embed.add_field(
        name="**Statistics**",
        value=(
            f"✅ **Catches Taken:** {catches_taken}\n"
            f"❌ **Catches Dropped:** {catches_dropped}\n"
            f"🎯 **Total Opportunities:** {total_opportunities}\n"
            f"📊 **Catch Success Rate:** {catch_percentage}%"
        ),
        inline=False
    )

    guild_stats = data_store.stats.get(guild_id, {})
    catch_list = []
    for uid, ustats in guild_stats.items():
        ustats = ensure_backward_compatibility(ustats)
        utaken = ustats['catches_taken']
        udropped = ustats['catches_dropped']
        if utaken + udropped >= MIN_CATCH_OPPORTUNITIES:
            catch_list.append((uid, utaken))

    catch_list.sort(key=lambda x: x[1], reverse=True)

    rank = 0
    total_qualified = len(catch_list)
    for idx, (uid, _) in enumerate(catch_list, 1):
        if uid == user_id:
            rank = idx
            break

    # Display ranking
    if rank > 0:
        if rank == 1:
            rank_emoji = "🥇"
            rank_text = "1st Place!"
        elif rank == 2:
            rank_emoji = "🥈"
            rank_text = "2nd Place"
        elif rank == 3:
            rank_emoji = "🥉"
            rank_text = "3rd Place"
        else:
            rank_emoji = "📊"
            rank_text = f"{rank} of {total_qualified}"

        embed.add_field(
            name="**Server Ranking**",
            value=f"{rank_emoji} **{rank_text}**",
            inline=False
        )
    elif total_opportunities < MIN_CATCH_OPPORTUNITIES:
        embed.add_field(
            name="**Server Ranking**",
            value="⏳ **Not Ranked**",
            inline=False
        )

    # Fun motivational message
    if catch_percentage == 100:
        footer_msg = "Perfect record! 🌟"
    elif catch_percentage >= 90:
        footer_msg = "Elite fielding! 🔥"
    elif catch_percentage >= 75:
        footer_msg = "Reliable hands! 💪"
    elif catch_percentage >= 50:
        footer_msg = "Keep improving! 📈"
    else:
        footer_msg = "Practice makes perfect! 🎯"

    embed.set_footer(text=footer_msg)

    return embed


# Leaderboard helper function

def get_qualified_players_count(guild_id: str, category: str, archived_stats: Dict = None) -> int:
    """
    Get count of qualified players for a specific leaderboard category
    Used for pagination button logic

    Args:
        guild_id: Discord guild ID
        category: Leaderboard category
        archived_stats: Optional archived stats dict (if viewing archived tournament)

    Returns:
        Number of players who qualify for this leaderboard
    """
    # Use archived stats if provided, otherwise use current stats
    stats = archived_stats if archived_stats else data_store.stats.get(guild_id, {})

    if not stats:
        return 0

    # Category definitions
    category_map = {
        'fantasy': ('Fantasy Points', lambda s: calculate_fantasy(s, calculate_batting_rating(s), calculate_bowling_rating(s))),
        'matches': ('Matches', lambda s: s.get('matches', max(s['innings_bat'], s['innings_bowl']))),
        'runs': ('Runs', lambda s: s['runs']),
        'wickets': ('Wickets', lambda s: s['wickets']),
        'strike_rate': ('Strike Rate', lambda s: calculate_strike_rate(s['runs'], s['balls_played'])),
        'catches_taken': ('Catches Taken', lambda s: s.get('catches_taken', 0)),
        'catches_dropped': ('Catches Dropped', lambda s: s.get('catches_dropped', 0)),
        'catch_success': ('Catch Success Rate', lambda s: calculate_catch_percentage(s.get('catches_taken', 0), s.get('catches_dropped', 0))),
        'bat_avg': ('Batting Average', lambda s: calculate_average(s['runs'], s['dismissals'])),
        'bowl_avg': ('Bowling Average', lambda s: calculate_bowling_avg(s['runs_conceded'], s['wickets'])),
        'high_score': ('High Score', lambda s: s['high_score']),
        'most_wickets': ('Best Bowling', lambda s: s.get('best_bowling', 0)),
        'hundreds': ('100s', lambda s: s['hundreds']),
        'fifties': ('50s', lambda s: s['fifties']),
        'three_fers': ('3-Fers', lambda s: s['three_fers']),
        'four_fers': ('4-Fers', lambda s: s.get('four_fers', 0)),
        'ducks': ('Ducks', lambda s: s['ducks']),
        'runs_conceded': ('Runs Conceded', lambda s: s['runs_conceded']),
        'balls_bowled': ('Balls Bowled', lambda s: s['balls_bowled']),
        'balls_played': ('Balls Played', lambda s: s['balls_played'])
    }

    cat_name, cat_func = category_map.get(category, category_map['runs'])

    qualified_count = 0
    for user_id, user_stats in stats.items():
        user_stats = ensure_backward_compatibility(user_stats)

        value = cat_func(user_stats)

        if value == 0:
            continue

        if category == 'catch_success':
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if category in ['catches_taken', 'catches_dropped']:
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if category == 'strike_rate':
            if user_stats.get('balls_played', 0) < MIN_BALLS_FOR_STRIKE_RATE:
                continue

        qualified_count += 1

    return qualified_count

# Leaderboard embeds (current)

def create_leaderboard_embed(guild_id: str, category: str, page: int,
                            guild: discord.Guild) -> discord.Embed:
    """
    Create leaderboard embed for specific category (CURRENT TOURNAMENT)

    Args:
        guild_id: Discord guild ID
        category: Leaderboard category
        page: Page number (0-indexed)
        guild: Discord guild object

    Returns:
        Discord embed with leaderboard
    """
    stats = data_store.stats.get(guild_id, {})

    if not stats:
        embed = discord.Embed(
            title="🏆 Hand Cricket Leaderboard",
            description="No statistics recorded yet!",
            color=discord.Color.gold()
        )
        return embed


    # Category definitions
    category_map = {
        'fantasy': ('Fantasy Points', lambda s: calculate_fantasy(s, calculate_batting_rating(s), calculate_bowling_rating(s))),
        'matches': ('Matches', lambda s: s.get('matches', max(s['innings_bat'], s['innings_bowl']))),
        'runs': ('Runs', lambda s: s['runs']),
        'wickets': ('Wickets', lambda s: s['wickets']),
        'strike_rate': ('Strike Rate', lambda s: calculate_strike_rate(s['runs'], s['balls_played'])),
        'catches_taken': ('Catches Taken', lambda s: s.get('catches_taken', 0)),
        'catches_dropped': ('Catches Dropped', lambda s: s.get('catches_dropped', 0)),
        'catch_success': ('Catch Success Rate', lambda s: calculate_catch_percentage(s.get('catches_taken', 0), s.get('catches_dropped', 0))),
        'bat_avg': ('Batting Average', lambda s: calculate_average(s['runs'], s['dismissals'])),
        'bowl_avg': ('Bowling Average', lambda s: calculate_bowling_avg(s['runs_conceded'], s['wickets'])),
        'high_score': ('High Score', lambda s: s['high_score']),
        'most_wickets': ('Best Bowling', lambda s: s.get('best_bowling', 0)),
        'hundreds': ('100s', lambda s: s['hundreds']),
        'fifties': ('50s', lambda s: s['fifties']),
        'three_fers': ('3-Fers', lambda s: s['three_fers']),
        'four_fers': ('4-Fers', lambda s: s.get('four_fers', 0)),
        'ducks': ('Ducks', lambda s: s['ducks']),
        'runs_conceded': ('Runs Conceded', lambda s: s['runs_conceded']),
        'balls_bowled': ('Balls Bowled', lambda s: s['balls_bowled']),
        'balls_played': ('Balls Played', lambda s: s['balls_played'])
    }

    cat_name, cat_func = category_map.get(category, category_map['runs'])

    # Sort players with UNIVERSAL ZERO FILTERING
    sorted_players = []
    for user_id, user_stats in stats.items():
        user_stats = ensure_backward_compatibility(user_stats)

        value = cat_func(user_stats)

        if value == 0:
            continue

        if category == 'catch_success':
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if category in ['catches_taken', 'catches_dropped']:
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if category == 'strike_rate':
            if user_stats.get('balls_played', 0) < MIN_BALLS_FOR_STRIKE_RATE:
                continue

        sorted_players.append((user_id, value, user_stats))


    # Bowling average: lower is better (ascending order)
    reverse_sort = category != 'bowl_avg'
    sorted_players.sort(key=lambda x: x[1], reverse=reverse_sort)

    # Pagination (9 per page)
    start_idx = page * 9
    end_idx = start_idx + 9
    page_players = sorted_players[start_idx:end_idx]

    embed = discord.Embed(
        title=f"🏆 Hand Cricket Leaderboard - {cat_name}",
        color=discord.Color.gold()
    )

    # Top 3 (only on first page AND if we have 3+ players)
    if page == 0 and len(sorted_players) >= 3:
        top3 = "✨ **Top Performers** ✨\n"
        for i in range(3):
            user_id, value, _ = sorted_players[i]
            member = guild.get_member(int(user_id))
            username = member.name if member else f"User {user_id}"

            if category == 'catch_success':
                top3 += f"{i+1}. {username} • {value}%\n"
            else:
                top3 += f"{i+1}. {username} • {value}\n"

        embed.add_field(name="", value=top3, inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━", value="", inline=False)

    # Rest of page
    leaderboard = ""
    for idx, (user_id, value, _) in enumerate(page_players):
        rank = start_idx + idx + 1

        if page == 0 and rank <= 3 and len(sorted_players) >= 3:
            continue

        member = guild.get_member(int(user_id))
        username = member.name if member else f"User {user_id}"

        if category == 'catch_success':
            leaderboard += f"{rank}. {username} • {value}%\n"
        else:
            leaderboard += f"{rank}. {username} • {value}\n"

    if leaderboard:
        embed.add_field(name="", value=leaderboard, inline=False)
    elif page == 0 and len(sorted_players) < 3:
        simple_list = ""
        for idx, (user_id, value, _) in enumerate(sorted_players, 1):
            member = guild.get_member(int(user_id))
            username = member.name if member else f"User {user_id}"

            if category == 'catch_success':
                simple_list += f"{idx}. {username} • {value}%\n"
            else:
                simple_list += f"{idx}. {username} • {value}\n"

        embed.add_field(name="", value=simple_list, inline=False)

    total_pages = (len(sorted_players) - 1) // 9 + 1 if sorted_players else 1
    embed.set_footer(text=f"Page {page + 1}/{total_pages} • Total Players: {len(sorted_players)}")

    return embed

# Leaderboard embeds (archived)

def create_archived_leaderboard_embed(guild_id: str, tournament_name: str, category: str,
                                     page: int, guild: discord.Guild) -> discord.Embed:
    """
    Create leaderboard embed for archived tournament

    Args:
        guild_id: Discord guild ID
        tournament_name: Name of archived tournament
        category: Leaderboard category
        page: Page number (0-indexed)
        guild: Discord guild object

    Returns:
        Discord embed with archived leaderboard
    """
    stats = data_store.load_tournament_stats(guild_id, tournament_name)

    if not stats:
        embed = discord.Embed(
            title="🏆 Hand Cricket Leaderboard",
            description=f"No statistics found for **{tournament_name}**!",
            color=discord.Color.gold()
        )
        return embed

    # Category definitions
    category_map = {
        'fantasy': ('Fantasy Points', lambda s: calculate_fantasy(s, calculate_batting_rating(s), calculate_bowling_rating(s))),
        'matches': ('Matches', lambda s: s.get('matches', max(s['innings_bat'], s['innings_bowl']))),
        'runs': ('Runs', lambda s: s['runs']),
        'wickets': ('Wickets', lambda s: s['wickets']),
        'strike_rate': ('Strike Rate', lambda s: calculate_strike_rate(s['runs'], s['balls_played'])),
        'catches_taken': ('Catches Taken', lambda s: s.get('catches_taken', 0)),
        'catches_dropped': ('Catches Dropped', lambda s: s.get('catches_dropped', 0)),
        'catch_success': ('Catch Success Rate', lambda s: calculate_catch_percentage(s.get('catches_taken', 0), s.get('catches_dropped', 0))),
        'bat_avg': ('Batting Average', lambda s: calculate_average(s['runs'], s['dismissals'])),
        'bowl_avg': ('Bowling Average', lambda s: calculate_bowling_avg(s['runs_conceded'], s['wickets'])),
        'high_score': ('High Score', lambda s: s['high_score']),
        'most_wickets': ('Best Bowling', lambda s: s.get('best_bowling', 0)),
        'hundreds': ('100s', lambda s: s['hundreds']),
        'fifties': ('50s', lambda s: s['fifties']),
        'three_fers': ('3-Fers', lambda s: s['three_fers']),
        'four_fers': ('4-Fers', lambda s: s.get('four_fers', 0)),
        'ducks': ('Ducks', lambda s: s['ducks']),
        'runs_conceded': ('Runs Conceded', lambda s: s['runs_conceded']),
        'balls_bowled': ('Balls Bowled', lambda s: s['balls_bowled']),
        'balls_played': ('Balls Played', lambda s: s['balls_played'])
    }

    cat_name, cat_func = category_map.get(category, category_map['runs'])

    sorted_players = []
    for user_id, user_stats in stats.items():
        user_stats = ensure_backward_compatibility(user_stats)

        value = cat_func(user_stats)

        if value == 0:
            continue

        if category == 'catch_success':
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if category in ['catches_taken', 'catches_dropped']:
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if category == 'strike_rate':
            if user_stats.get('balls_played', 0) < MIN_BALLS_FOR_STRIKE_RATE:
                continue

        sorted_players.append((user_id, value, user_stats))

    # Bowling average: lower is better (ascending order)
    reverse_sort = category != 'bowl_avg'
    sorted_players.sort(key=lambda x: x[1], reverse=reverse_sort)

    # Pagination (9 per page)
    start_idx = page * 9
    end_idx = start_idx + 9
    page_players = sorted_players[start_idx:end_idx]

    embed = discord.Embed(
        title=f"🏆 Hand Cricket Leaderboard - {cat_name}",
        color=discord.Color.gold()
    )

    # Top 3 (only on first page AND if we have 3+ players)
    if page == 0 and len(sorted_players) >= 3:
        top3 = "✨ **Top Performers** ✨\n"
        for i in range(3):
            user_id, value, _ = sorted_players[i]
            member = guild.get_member(int(user_id))
            username = member.name if member else f"User {user_id}"

            if category == 'catch_success':
                top3 += f"{i+1}. {username} • {value}%\n"
            else:
                top3 += f"{i+1}. {username} • {value}\n"

        embed.add_field(name="", value=top3, inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━", value="", inline=False)

    # Rest of page
    leaderboard = ""
    for idx, (user_id, value, _) in enumerate(page_players):
        rank = start_idx + idx + 1

        if page == 0 and rank <= 3 and len(sorted_players) >= 3:
            continue

        member = guild.get_member(int(user_id))
        username = member.name if member else f"User {user_id}"

        if category == 'catch_success':
            leaderboard += f"{rank}. {username} • {value}%\n"
        else:
            leaderboard += f"{rank}. {username} • {value}\n"

    if leaderboard:
        embed.add_field(name="", value=leaderboard, inline=False)
    elif page == 0 and len(sorted_players) < 3:
        simple_list = ""
        for idx, (user_id, value, _) in enumerate(sorted_players, 1):
            member = guild.get_member(int(user_id))
            username = member.name if member else f"User {user_id}"

            if category == 'catch_success':
                simple_list += f"{idx}. {username} • {value}%\n"
            else:
                simple_list += f"{idx}. {username} • {value}\n"

        embed.add_field(name="", value=simple_list, inline=False)

    total_pages = (len(sorted_players) - 1) // 9 + 1 if sorted_players else 1
    embed.set_footer(text=f"Page {page + 1}/{total_pages} • Total Players: {len(sorted_players)} • 📜 ARCHIVED")

    return embed

# Channel status embeds

def create_channel_status_embed(guild_id: str, page: int, guild: discord.Guild) -> discord.Embed:
    """Create channel status embed with pagination"""

    server_enabled = data_store.is_auto_catch_enabled(guild_id)

    data_store.init_guild(guild_id)
    auto_catch_channels = data_store.guilds[guild_id].get('auto_catch_channels', {})

    enabled_channels = []
    disabled_channels = []

    for channel_id, enabled in auto_catch_channels.items():
        channel = guild.get_channel(int(channel_id))
        if channel:
            if enabled:
                enabled_channels.append(channel.mention)
            else:
                disabled_channels.append(channel.mention)

    embed = discord.Embed(
        title="📊 Channel Status",
        color=discord.Color.blue()
    )

    server_status = "✅ **Enabled**" if server_enabled else "❌ **Disabled**"
    embed.add_field(
        name="Server Status",
        value=server_status,
        inline=False
    )

    start_idx = page * 10
    end_idx = start_idx + 10
    page_enabled = enabled_channels[start_idx:end_idx]

    total_pages = (len(enabled_channels) - 1) // 10 + 1 if enabled_channels else 1

    if page_enabled:
        channels_text = "\n".join(f"✅ {ch}" for ch in page_enabled)
        embed.add_field(
            name=f"Enabled Channels ({len(enabled_channels)} total)",
            value=channels_text,
            inline=False
        )
    elif page == 0:
        embed.add_field(
            name="Enabled Channels (0)",
            value="*No channels enabled yet*",
            inline=False
        )

    if page == total_pages - 1 and disabled_channels:
        channels_text = "\n".join(f"❌ {ch}" for ch in disabled_channels[:5])
        if len(disabled_channels) > 5:
            channels_text += f"\n*...and {len(disabled_channels) - 5} more*"
        embed.add_field(
            name=f"Disabled Channels ({len(disabled_channels)})",
            value=channels_text,
            inline=False
        )

    if total_pages > 1:
        embed.set_footer(text=f"Page {page + 1}/{total_pages} • Use buttons to navigate")
    elif server_enabled and enabled_channels:
        embed.set_footer(text="✅ Auto-catch is active in enabled channels!")
    elif server_enabled and not enabled_channels:
        embed.set_footer(text="⚠️ Server enabled, but no channels enabled yet!")
    else:
        embed.set_footer(text="🔴 Server disabled - enable with +enable first")

    return embed

# Recent performances embed

def create_recent_performances_embed(user_id: str, guild_id: str, guild: discord.Guild, page: int = 0) -> discord.Embed:
    """
    Create beautiful recent performances embed

    Args:
        user_id: Discord user ID
        guild_id: Discord guild ID
        guild: Discord guild object
        page: Page number (0-indexed, 5 matches per page)

    Returns:
        Discord embed with recent match performances
    """
    from core.match_history import match_history

    member = guild.get_member(int(user_id))
    username = member.name if member else f"User {user_id}"

    player_matches = match_history.get_player_matches(guild_id, user_id)

    if not player_matches:
        embed = discord.Embed(
            title=f"📋 {username}'s Recent Performances",
            description="No match history found yet!",
            color=discord.Color.light_gray()
        )
        if member:
            embed.set_thumbnail(url=member.display_avatar.url)
        return embed

    player_matches = list(reversed(player_matches))

    start_idx = page * 5
    end_idx = start_idx + 5
    page_matches = player_matches[start_idx:end_idx]

    total_pages = (len(player_matches) - 1) // 5 + 1

    embed = discord.Embed(
        title=f"📋 {username}'s Recent Performances",
        color=discord.Color.blue()
    )

    if member:
        embed.set_thumbnail(url=member.display_avatar.url)

    for i, match in enumerate(page_matches, start=start_idx + 1):
        stats = match['stats']

        match_number = len(player_matches) - start_idx - (i - start_idx - 1)

        batting_text = ""
        if stats.get('balls_played', 0) > 0:
            not_out_symbol = "*" if stats.get('not_out', 0) == 1 else ""
            batting_text = (
                f"**RUNS:** {stats['runs']}{not_out_symbol}\n"
                f"**BALLS:** {stats['balls_played']}"
            )
        else:
            batting_text = "**DNB**"

        bowling_text = ""
        if stats.get('balls_bowled', 0) > 0:
            bowling_text = (
                f"**RUNS:** {stats['runs_conceded']}\n"
                f"**BALLS:** {stats['balls_bowled']}\n"
                f"**WICKETS:** {stats['wickets']}"
            )
        else:
            bowling_text = "**DNB**"

        embed.add_field(
            name=f"MATCH {match_number}",
            value="",
            inline=False
        )

        embed.add_field(
            name="🏏 BATTING",
            value=batting_text,
            inline=True
        )

        embed.add_field(
            name="⚾ BOWLING",
            value=bowling_text,
            inline=True
        )

        embed.add_field(name="", value="", inline=True)

    embed.set_footer(text=f"Page {page + 1}/{total_pages}")

    return embed


def create_all_time_stats_embed(user_id: str, combined_stats: Dict, category: str,
                                tournament_count: int, guild: discord.Guild) -> discord.Embed:
    """
    Create all-time statistics embed for a category

    Args:
        user_id: Discord user ID
        combined_stats: Combined statistics dictionary
        category: Category name (BPSL, BOTS, etc.)
        tournament_count: Number of tournaments in category
        guild: Discord guild object

    Returns:
        Discord embed with all-time statistics
    """
    member = guild.get_member(int(user_id))
    username = member.name if member else f"User {user_id}"

    # Ensure backward compatibility
    stats = ensure_backward_compatibility(combined_stats)

    bat_avg = calculate_average(stats['runs'], stats['dismissals'])
    strike_rate = calculate_strike_rate(stats['runs'], stats['balls_played'])
    bowl_avg = calculate_bowling_avg(stats['runs_conceded'], stats['wickets'])
    economy = calculate_economy(stats['runs_conceded'], stats['balls_bowled'])

    bat_rating = calculate_batting_rating(stats)
    bowl_rating = calculate_bowling_rating(stats)
    overall_rating = calculate_overall_rating(bat_rating, bowl_rating)
    fantasy = calculate_fantasy(stats, bat_rating, bowl_rating)

    role_name, role_emoji = get_role_emoji(bat_rating, bowl_rating)

    # Total matches
    total_matches = stats.get('matches', max(stats['innings_bat'], stats['innings_bowl']))

    # Show category in BOLD, or "All-Time Stats" if no category
    category_display = f"**{category}**" if category else "All-Time Stats"

    embed = discord.Embed(
        title=f"{username}'s Hand Cricket Stats",
        description=f"{category_display} | Matches: {total_matches} | Fantasy: {fantasy}\n{role_name} {role_emoji} {overall_rating} | Bat: {bat_rating} | Bowl: {bowl_rating}",
        color=discord.Color.blue()
    )

    if member:
        embed.set_thumbnail(url=member.display_avatar.url)

    # Batting statistics

    # Show * if player has not outs and never been dismissed
    avg_display = f"{bat_avg}*" if stats['dismissals'] == 0 and stats['innings_bat'] > 0 else str(bat_avg)

    batting = (
        f"🏏 **Innings:** {stats['innings_bat']}\n"
        f"💥 **Runs:** {stats['runs']}\n"
        f"⚾ **Balls:** {stats['balls_played']}\n"
        f"📊 **Avg:** {avg_display}\n"
        f"⚡ **SR:** {strike_rate}\n"
        f"🌟 **50s:** {stats['fifties']}\n"
        f"💯 **100s:** {stats['hundreds']}\n"
        f"🦆 **Ducks:** {stats['ducks']}\n"
        f"🏆 **High Score:** {stats['high_score']}"
    )

    # Bowling statistics
    bowling = (
        f"🎳 **Innings:** {stats['innings_bowl']}\n"
        f"🎯 **Wickets:** {stats['wickets']}\n"
        f"⚾ **Balls:** {stats['balls_bowled']}\n"
        f"📊 **Avg:** {bowl_avg}\n"
        f"💰 **Eco:** {economy}\n"
        f"🥉 **3w:** {stats['three_fers']}\n"
        f"🥇 **4w:** {stats['four_fers']}\n"
        f"🏃 **Runs Conceded:** {stats['runs_conceded']}\n"
        f"🌟 **Best:** {stats['best_bowling']}"
    )

    embed.add_field(name="Batting", value=batting, inline=True)
    embed.add_field(name="Bowling", value=bowling, inline=True)

    # FIELDING STATISTICS (if any)
    catches_taken = stats.get('catches_taken', 0)
    catches_dropped = stats.get('catches_dropped', 0)

    if catches_taken > 0 or catches_dropped > 0:
        catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)
        embed.add_field(
            name="Fielding",
            value=f"🧤 **Caught:** {catches_taken} | 🚫 **Dropped:** {catches_dropped} | 📊 **Success:** {catch_percentage}%",
            inline=False
        )

    embed.set_footer(text="All-Time Career Statistics")

    return embed


def create_all_time_leaderboard_embed(guild_id: str, category: str, combined_stats: Dict,
                                     tournament_count: int, leaderboard_category: str,
                                     page: int, guild: discord.Guild) -> discord.Embed:
    """
    Create all-time leaderboard embed for a category

    Args:
        guild_id: Discord guild ID
        category: Tournament category (BPSL, BOTS, etc.)
        combined_stats: Combined statistics for all players
        tournament_count: Number of tournaments
        leaderboard_category: Stat category to rank by (runs, wickets, etc.)
        page: Page number (0-indexed)
        guild: Discord guild object

    Returns:
        Discord embed with all-time leaderboard
    """
    if not combined_stats:
        embed = discord.Embed(
            title=f"🏆 {category} All Time Leaderboard",
            description="No statistics recorded yet!",
            color=discord.Color.gold()
        )
        return embed

    # Category definitions (same as regular leaderboard)
    category_map = {
        'fantasy': ('Fantasy Points', lambda s: calculate_fantasy(s, calculate_batting_rating(s), calculate_bowling_rating(s))),
        'matches': ('Matches', lambda s: s.get('matches', max(s['innings_bat'], s['innings_bowl']))),
        'runs': ('Runs', lambda s: s['runs']),
        'wickets': ('Wickets', lambda s: s['wickets']),
        'strike_rate': ('Strike Rate', lambda s: calculate_strike_rate(s['runs'], s['balls_played'])),
        'catches_taken': ('Catches Taken', lambda s: s.get('catches_taken', 0)),
        'catches_dropped': ('Catches Dropped', lambda s: s.get('catches_dropped', 0)),
        'catch_success': ('Catch Success Rate', lambda s: calculate_catch_percentage(s.get('catches_taken', 0), s.get('catches_dropped', 0))),
        'bat_avg': ('Batting Average', lambda s: calculate_average(s['runs'], s['dismissals'])),
        'bowl_avg': ('Bowling Average', lambda s: calculate_bowling_avg(s['runs_conceded'], s['wickets'])),
        'high_score': ('High Score', lambda s: s['high_score']),
        'most_wickets': ('Best Bowling', lambda s: s.get('best_bowling', 0)),
        'hundreds': ('100s', lambda s: s['hundreds']),
        'fifties': ('50s', lambda s: s['fifties']),
        'three_fers': ('3-Fers', lambda s: s['three_fers']),
        'four_fers': ('4-Fers', lambda s: s.get('four_fers', 0)),
        'ducks': ('Ducks', lambda s: s['ducks']),
        'runs_conceded': ('Runs Conceded', lambda s: s['runs_conceded']),
        'balls_bowled': ('Balls Bowled', lambda s: s['balls_bowled']),
        'balls_played': ('Balls Played', lambda s: s['balls_played'])
    }

    cat_name, cat_func = category_map.get(leaderboard_category, category_map['runs'])

    # Sort players with UNIVERSAL ZERO FILTERING
    sorted_players = []
    for user_id, user_stats in combined_stats.items():
        user_stats = ensure_backward_compatibility(user_stats)

        value = cat_func(user_stats)

        if value == 0:
            continue

        # Apply minimum requirements for certain categories
        if leaderboard_category == 'catch_success':
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if leaderboard_category in ['catches_taken', 'catches_dropped']:
            total_opps = user_stats.get('catches_taken', 0) + user_stats.get('catches_dropped', 0)
            if total_opps < MIN_CATCH_OPPORTUNITIES:
                continue

        if leaderboard_category == 'strike_rate':
            if user_stats.get('balls_played', 0) < MIN_BALLS_FOR_STRIKE_RATE:
                continue

        sorted_players.append((user_id, value, user_stats))

    # Bowling average: lower is better (ascending order)
    reverse_sort = leaderboard_category != 'bowl_avg'
    sorted_players.sort(key=lambda x: x[1], reverse=reverse_sort)

    # Pagination (9 per page)
    start_idx = page * 9
    end_idx = start_idx + 9
    page_players = sorted_players[start_idx:end_idx]

    embed = discord.Embed(
        title=f"🏆 {category} All Time-Leaderboard - {cat_name}",
        color=discord.Color.gold()
    )

    # Top 3 (only on first page AND if we have 3+ players)
    if page == 0 and len(sorted_players) >= 3:
        top3 = "✨ **Top Performers** ✨\n"
        for i in range(3):
            user_id, value, _ = sorted_players[i]
            member = guild.get_member(int(user_id))
            username = member.name if member else f"User {user_id}"

            if leaderboard_category == 'catch_success':
                top3 += f"{i+1}. {username} • {value}%\n"
            else:
                top3 += f"{i+1}. {username} • {value}\n"

        embed.add_field(name="", value=top3, inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━", value="", inline=False)

    # Rest of page
    leaderboard = ""
    for idx, (user_id, value, _) in enumerate(page_players):
        rank = start_idx + idx + 1

        if page == 0 and rank <= 3 and len(sorted_players) >= 3:
            continue

        member = guild.get_member(int(user_id))
        username = member.name if member else f"User {user_id}"

        if leaderboard_category == 'catch_success':
            leaderboard += f"{rank}. {username} • {value}%\n"
        else:
            leaderboard += f"{rank}. {username} • {value}\n"

    if leaderboard:
        embed.add_field(name="", value=leaderboard, inline=False)
    elif page == 0 and len(sorted_players) < 3:
        simple_list = ""
        for idx, (user_id, value, _) in enumerate(sorted_players, 1):
            member = guild.get_member(int(user_id))
            username = member.name if member else f"User {user_id}"

            if leaderboard_category == 'catch_success':
                simple_list += f"{idx}. {username} • {value}%\n"
            else:
                simple_list += f"{idx}. {username} • {value}\n"

        embed.add_field(name="", value=simple_list, inline=False)

    total_pages = (len(sorted_players) - 1) // 9 + 1 if sorted_players else 1
    embed.set_footer(text=f"Page {page + 1}/{total_pages} • Total Players: {len(sorted_players)}")

    return embed
