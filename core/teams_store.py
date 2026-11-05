"""
Teams Data Storage Module
Handles team information, logos, and match results for points table
"""

import json
import os
from typing import Dict, List

class TeamsStore:
    """
    Manages team data for points table system
    Separate from main stats to keep it isolated
    """

    def __init__(self):
        self.teams = {}  # guild_id: {team_name: {color, logo, stats}}
        self.data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'teams_data.json')
        self.logo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'team_logos')

        # Create logo directory if it doesn't exist
        os.makedirs(self.logo_dir, exist_ok=True)

        self.load_data()

    def load_data(self):
        """Load team data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                self.teams = json.load(f)
            print("✅ Teams data loaded successfully")
        except FileNotFoundError:
            print("⚠️ No teams data file found. Starting fresh.")
        except json.JSONDecodeError:
            print("❌ Teams data file corrupted. Starting fresh.")

    def save_data(self):
        """Save team data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.teams, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving teams data: {e}")

    def guild_has_teams(self, guild_id: str) -> bool:
        """Check if guild has teams set up"""
        return guild_id in self.teams and len(self.teams[guild_id]) > 0

    def get_teams(self, guild_id: str) -> Dict:
        """Get all teams for a guild"""
        return self.teams.get(guild_id, {})

    def get_teams_list(self, guild_id: str) -> List[Dict]:
        """
        Get teams as list sorted by points
        Returns list of dicts ready for graphic generation
        """
        if guild_id not in self.teams:
            return []

        teams_list = []
        for team_name, team_data in self.teams[guild_id].items():
            teams_list.append({
                'name': team_name,
                'color': tuple(team_data['color']),  # Convert list back to tuple
                'logo': team_data['logo'],
                'played': team_data['played'],
                'won': team_data['won'],
                'lost': team_data['lost'],
                'points': team_data['points']
            })

        # Sort by points (desc), then wins (desc)
        teams_list.sort(key=lambda x: (x['points'], x['won']), reverse=True)
        return teams_list

    def init_guild_teams(self, guild_id: str, teams_data: Dict):
        """
        Initialize teams for a guild

        Args:
            guild_id: Discord guild ID
            teams_data: Dict of {team_name: {color, logo}}
        """
        self.teams[guild_id] = {}

        for team_name, data in teams_data.items():
            self.teams[guild_id][team_name] = {
                'color': data['color'],  # RGBA tuple as list
                'logo': data['logo'],     # Filename
                'played': 0,
                'won': 0,
                'lost': 0,
                'points': 0
            }

        self.save_data()

    def reset_guild_teams(self, guild_id: str):
        """Delete all teams for a guild"""
        if guild_id in self.teams:
            del self.teams[guild_id]
            self.save_data()

    def record_match_result(self, guild_id: str, winner: str, loser: str):
        """
        Record a match result
        Winner gets +2 points, +1 win
        Loser gets +1 match played, +1 loss
        """
        if guild_id not in self.teams:
            return False

        if winner not in self.teams[guild_id] or loser not in self.teams[guild_id]:
            return False

        self.teams[guild_id][winner]['played'] += 1
        self.teams[guild_id][winner]['won'] += 1
        self.teams[guild_id][winner]['points'] += 2

        self.teams[guild_id][loser]['played'] += 1
        self.teams[guild_id][loser]['lost'] += 1

        self.save_data()
        return True

    def get_logo_path(self, filename: str) -> str:
        """Get full path to team logo"""
        return os.path.join(self.logo_dir, filename)

# Global teams store instance
teams_store = TeamsStore()
