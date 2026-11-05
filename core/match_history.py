"""
Match History Storage Module
Stores individual match records for accurate stat removal and performance tracking
"""

import json
import os
from typing import Dict, List, Optional

class MatchHistory:
    """
    Manages individual match records for each player
    Enables accurate stat removal and performance tracking
    """

    def __init__(self):
        self.matches = {}  # guild_id: [match_records]
        self.data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'match_history.json')
        self.load_data()

    def load_data(self):
        """Load match history from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                self.matches = json.load(f)
            print("✅ Match history loaded successfully")
        except FileNotFoundError:
            print("⚠️ No match history file found. Starting fresh.")
        except json.JSONDecodeError:
            print("❌ Match history file corrupted. Starting fresh.")

    def save_data(self):
        """Save match history to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.matches, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving match history: {e}")

    def add_match(self, guild_id: str, match_data: Dict):
        """Add a new match record"""
        if guild_id not in self.matches:
            self.matches[guild_id] = []

        self.matches[guild_id].append(match_data)
        self.save_data()

    def get_latest_match(self, guild_id: str) -> Optional[Dict]:
        """Get the most recent match for a guild"""
        if guild_id not in self.matches or not self.matches[guild_id]:
            return None

        return self.matches[guild_id][-1]

    def remove_latest_match(self, guild_id: str) -> Optional[Dict]:
        """Remove the most recent match"""
        if guild_id not in self.matches or not self.matches[guild_id]:
            return None

        removed = self.matches[guild_id].pop()
        self.save_data()
        return removed

    def get_player_matches(self, guild_id: str, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get all matches for a specific player"""
        if guild_id not in self.matches:
            return []

        player_matches = []

        for match in self.matches[guild_id]:
            for player in match['players']:
                if player['user_id'] == user_id:
                    player_matches.append({
                        'match_id': match['match_id'],
                        'timestamp': match['timestamp'],
                        'stats': player
                    })
                    break

        if limit:
            return player_matches[-limit:]

        return player_matches

    def recalculate_player_stats(self, guild_id: str, user_id: str) -> Dict:
        """Recalculate all stats for a player from match history"""
        player_matches = self.get_player_matches(guild_id, user_id)

        stats = {
            'matches': 0,
            'innings_bat': 0,
            'runs': 0,
            'balls_played': 0,
            'not_outs': 0,
            'innings_bowl': 0,
            'runs_conceded': 0,
            'balls_bowled': 0,
            'wickets': 0,
            'high_score': 0,
            'best_bowling': 0,
            'fifties': 0,
            'hundreds': 0,
            'ducks': 0,
            'three_fers': 0,
            'four_fers': 0,
            'dismissals': 0,
            'catches_taken': 0,
            'catches_dropped': 0
        }

        stats['matches'] = len(player_matches)

        for match in player_matches:
            player_stats = match['stats']

            # Batting
            if player_stats.get('balls_played', 0) > 0:
                stats['innings_bat'] += 1
                stats['runs'] += player_stats['runs']
                stats['balls_played'] += player_stats['balls_played']

                if player_stats.get('not_out', 0) == 1:
                    stats['not_outs'] += 1

                if player_stats.get('not_out', 0) == 0:
                    stats['dismissals'] += 1
                    if player_stats['runs'] == 0:
                        stats['ducks'] += 1

                if player_stats['runs'] > stats['high_score']:
                    stats['high_score'] = player_stats['runs']

                if player_stats['runs'] >= 100:
                    stats['hundreds'] += 1
                elif player_stats['runs'] >= 50:
                    stats['fifties'] += 1

            # Bowling
            if player_stats.get('balls_bowled', 0) > 0:
                stats['innings_bowl'] += 1
                stats['runs_conceded'] += player_stats['runs_conceded']
                stats['balls_bowled'] += player_stats['balls_bowled']
                stats['wickets'] += player_stats['wickets']

                if player_stats['wickets'] > stats['best_bowling']:
                    stats['best_bowling'] = player_stats['wickets']

                if player_stats['wickets'] >= 4:
                    stats['four_fers'] += 1
                elif player_stats['wickets'] >= 3:
                    stats['three_fers'] += 1

        return stats

# Global instance
match_history = MatchHistory()
