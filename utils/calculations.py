"""
Statistics Calculation Module
Contains all formulas for calculating cricket statistics and ratings
"""

from typing import Dict, Tuple
from config import MAX_RATING

# Basic cricket statistics

def calculate_average(runs: int, dismissals: int) -> float:
    """
    Calculate batting average (Real cricket formula)

    Average = Total Runs / Number of Times Dismissed
    Not outs do NOT count as dismissals

    Args:
        runs: Total runs scored
        dismissals: Number of times dismissed (does NOT include not outs)

    Returns:
        Batting average (runs per dismissal)
    """
    if dismissals == 0:
        # If never dismissed, return runs with * indicator
        return float(runs)
    return round(runs / dismissals, 1)

def calculate_strike_rate(runs: int, balls: int) -> float:
    """
    Calculate batting strike rate

    Args:
        runs: Total runs scored
        balls: Total balls faced

    Returns:
        Strike rate (runs per 100 balls)
    """
    return round((runs / balls) * 100, 1) if balls > 0 else 0

def calculate_economy(runs: int, balls: int) -> float:
    """
    Calculate bowling economy rate

    Args:
        runs: Runs conceded
        balls: Balls bowled

    Returns:
        Economy rate (runs per over)
    """
    return round((runs / balls) * 6, 1) if balls > 0 else 0

def calculate_bowling_avg(runs: int, wickets: int) -> float:
    """
    Calculate bowling average

    Args:
        runs: Runs conceded
        wickets: Wickets taken

    Returns:
        Bowling average (runs per wicket)
    """
    return round(runs / wickets, 1) if wickets > 0 else 0

# Fielding statistics

def calculate_catch_percentage(taken: int, dropped: int) -> float:
    """
    Calculate catch success rate

    Args:
        taken: Number of catches taken
        dropped: Number of catches dropped

    Returns:
        Success rate as percentage
    """
    total = taken + dropped
    return round((taken / total) * 100, 1) if total > 0 else 0.0

def get_fielding_grade(catch_percentage: float) -> Tuple[str, str]:
    """
    Get fielding grade based on catch percentage

    Args:
        catch_percentage: Catch success rate

    Returns:
        Tuple of (grade_name, emoji)
    """
    if catch_percentage >= 90:
        return "Elite Fielder", "🥇"
    elif catch_percentage >= 75:
        return "Reliable Hands", "🥈"
    elif catch_percentage >= 60:
        return "Safe Pair", "🥉"
    elif catch_percentage >= 40:
        return "Needs Work", "⚠️"
    else:
        return "Butterfingers", "🦆"

# Player ratings system

def calculate_batting_rating(stats: Dict) -> int:
    """
    Calculate batting rating based on performance (capped at 99)

    Formula considers:
    - Batting average
    - Total runs
    - Balls played
    - Ducks
    - Not outs (bonus)
    - Fifties and hundreds

    Args:
        stats: Player statistics dictionary

    Returns:
        Batting rating (0-99)
    """
    bat_avg = calculate_average(stats['runs'], stats['dismissals'])

    rating = 50  # Base rating
    rating += bat_avg * 1.5  # Reward high average
    rating += stats['runs'] / 20  # Reward run accumulation
    rating -= stats['balls_played'] / 20  # Slight penalty for slow scoring
    rating -= stats['ducks'] * 12  # Penalty for ducks
    rating += stats.get('not_outs', 0) * 3  # bonus for not outs
    rating += stats['fifties'] * 7  # Reward for fifties
    rating += stats['hundreds'] * 15  # Higher reward for hundreds

    return min(MAX_RATING, max(0, int(round(rating))))

def calculate_bowling_rating(stats: Dict) -> int:
    """
    Calculate bowling rating based on performance (capped at 99)

    Formula considers:
    - Bowling average
    - Economy rate
    - Wickets taken
    - Three-fers and four-fers

    Args:
        stats: Player statistics dictionary

    Returns:
        Bowling rating (0-99)
    """
    bowl_avg = calculate_bowling_avg(stats['runs_conceded'], stats['wickets'])
    economy = calculate_economy(stats['runs_conceded'], stats['balls_bowled'])

    rating = 70  # Base rating
    rating -= bowl_avg / 2.25  # Penalty for high average
    rating += stats['wickets'] * 3.2  # Reward wickets
    rating -= max(0, economy - 6) * 2  # Penalty for economy > 6
    rating += stats['three_fers'] * 11  # Reward for 3-wicket hauls
    rating += stats.get('four_fers', 0) * 13  # Higher reward for 4-wicket hauls

    return min(MAX_RATING, max(0, int(round(rating))))

def calculate_overall_rating(bat_rating: int, bowl_rating: int) -> int:
    """
    Calculate overall player rating

    All-rounders (both ratings >= 75) get average of both
    Otherwise, use the higher rating

    Args:
        bat_rating: Batting rating
        bowl_rating: Bowling rating

    Returns:
        Overall rating (0-99)
    """
    if bat_rating >= 75 and bowl_rating >= 75:
        return min(MAX_RATING, int(round((bat_rating + bowl_rating) / 2)))
    else:
        return max(bat_rating, bowl_rating)

def get_role_emoji(bat_rating: int, bowl_rating: int) -> Tuple[str, str]:
    """
    Determine player role based on ratings

    Args:
        bat_rating: Batting rating
        bowl_rating: Bowling rating

    Returns:
        Tuple of (role_name, emoji)
    """
    if bat_rating >= 75 and bowl_rating >= 75:
        return "All-Rounder", "⚡"
    elif bat_rating > bowl_rating:
        return "Batsman", "🏏"
    else:
        return "Bowler", "⚾"

# Fantasy points system

def calculate_fantasy(stats: Dict, bat_rating: int, bowl_rating: int) -> int:
    """
    Calculate fantasy cricket points (no cap)

    Fantasy points are used for overall player comparison
    Considers all aspects of performance

    Args:
        stats: Player statistics dictionary
        bat_rating: Batting rating
        bowl_rating: Bowling rating

    Returns:
        Total fantasy points
    """
    fantasy = (bat_rating * bowl_rating) / 50
    fantasy += stats['runs'] / 6
    fantasy += stats['wickets'] * 5
    fantasy += stats['fifties'] * 7
    fantasy += stats['hundreds'] * 15
    fantasy += stats['three_fers'] * 11
    fantasy += stats.get('four_fers', 0) * 15
    fantasy -= stats['ducks'] * 8
    fantasy += stats['high_score'] / 10
    fantasy += stats['best_bowling'] * 4

    return int(round(fantasy))
