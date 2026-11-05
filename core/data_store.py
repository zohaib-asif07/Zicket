"""
Data Storage Module
Handles all data persistence operations for guild settings and player statistics
"""

import json
import os
from typing import Dict, List, Optional
from config import DEFAULT_TOURNAMENT

class DataStore:
    """
    Manages persistent storage of guild settings and player statistics
    Data is stored in JSON format
    NOW SUPPORTS TOURNAMENT ARCHIVES AND CATEGORIES
    """

    def __init__(self):
        self.guilds = {}  # guild_id: {prefix, logs_channel, allowed, tournament, tournament_category, auto_catch_enabled, auto_catch_channels}
        self.stats = {}   # guild_id: {user_id: stats_dict}
        self.maintenance_mode = False
        self.tournament_list = {}  # guild_id: [list of tournament names]
        self.data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot_data.json')
        self.tournament_list_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tournament_list.json')
        self.tournaments_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tournaments')

        # Create tournaments directory if it doesn't exist
        os.makedirs(self.tournaments_dir, exist_ok=True)

        self.load_data()
        self.load_tournament_list()

    def load_data(self):
        """Load data from JSON file on bot startup"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.guilds = data.get('guilds', {})
                self.stats = data.get('stats', {})
                self.maintenance_mode = data.get('maintenance_mode', False)
            print(f"✅ Data loaded successfully from {self.data_file}")
        except FileNotFoundError:
            print("⚠️  No existing data file found. Starting with fresh data.")
        except json.JSONDecodeError:
            print("❌ Error: Data file is corrupted. Starting with fresh data.")

    def load_tournament_list(self):
        """Load tournament list from JSON file"""
        try:
            with open(self.tournament_list_file, 'r') as f:
                self.tournament_list = json.load(f)
            print("✅ Tournament list loaded successfully")
        except FileNotFoundError:
            print("⚠️  No tournament list file found. Starting fresh.")
            self.tournament_list = {}
        except json.JSONDecodeError:
            print("❌ Error: Tournament list file corrupted. Starting fresh.")
            self.tournament_list = {}

    def save_data(self):
        """Save current data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump({
                    'guilds': self.guilds,
                    'stats': self.stats,
                    'maintenance_mode': self.maintenance_mode
                }, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving data: {e}")

    def save_tournament_list(self):
        """Save tournament list to JSON file"""
        try:
            with open(self.tournament_list_file, 'w') as f:
                json.dump(self.tournament_list, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving tournament list: {e}")

    def get_tournament_file_path(self, guild_id: str, tournament_name: str) -> str:
        """
        Get file path for tournament archive

        Args:
            guild_id: Discord guild ID
            tournament_name: Tournament name (spaces will be removed)

        Returns:
            Full path to tournament JSON file
        """
        clean_name = tournament_name.replace(' ', '').replace('/', '').replace('\\', '')
        filename = f"{guild_id}_{clean_name}.json"
        return os.path.join(self.tournaments_dir, filename)

    def archive_tournament(self, guild_id: str, tournament_name: str, category: str = None) -> bool:
        """
        Archive current tournament stats to separate file WITH CATEGORY

        Args:
            guild_id: Discord guild ID
            tournament_name: Name of tournament to archive
            category: Tournament category - uses current if None

        Returns:
            True if successful, False otherwise
        """
        try:
            guild_stats = self.stats.get(guild_id, {})

            if not guild_stats:
                print(f"⚠️  No stats to archive for guild {guild_id}")
                return False

            # Use current tournament category if not provided
            if category is None:
                self.init_guild(guild_id)
                category = self.guilds[guild_id].get('tournament_category', 'OTHER')

            archive_data = {
                'tournament_name': tournament_name,
                'guild_id': guild_id,
                'category': category.upper(),
                'stats': guild_stats
            }

            file_path = self.get_tournament_file_path(guild_id, tournament_name)
            with open(file_path, 'w') as f:
                json.dump(archive_data, f, indent=2)

            if guild_id not in self.tournament_list:
                self.tournament_list[guild_id] = []

            # Remove spaces for the list entry
            clean_name = tournament_name.replace(' ', '')

            if clean_name not in self.tournament_list[guild_id]:
                self.tournament_list[guild_id].append(clean_name)
                self.save_tournament_list()

            print(f"✅ Tournament '{tournament_name}' archived successfully (Category: {category})")
            return True

        except Exception as e:
            print(f"❌ Error archiving tournament: {e}")
            return False

    def load_tournament_stats(self, guild_id: str, tournament_name: str) -> Dict:
        """
        Load stats from archived tournament

        Args:
            guild_id: Discord guild ID
            tournament_name: Tournament name (with or without spaces)

        Returns:
            Dictionary of stats, or empty dict if not found
        """
        try:
            file_path = self.get_tournament_file_path(guild_id, tournament_name)

            if not os.path.exists(file_path):
                return {}

            with open(file_path, 'r') as f:
                archive_data = json.load(f)
                return archive_data.get('stats', {})

        except Exception as e:
            print(f"❌ Error loading tournament stats: {e}")
            return {}

    def get_tournament_list(self, guild_id: str) -> List[str]:
        """
        Get list of archived tournaments for a guild

        Args:
            guild_id: Discord guild ID

        Returns:
            List of tournament names
        """
        return self.tournament_list.get(guild_id, [])

    def init_guild(self, guild_id: str):
        """
        Initialize guild data with default values if not exists

        Args:
            guild_id: Discord guild ID as string
        """
        if guild_id not in self.guilds:
            self.guilds[guild_id] = {
                'prefix': '+',
                'logs_channel': None,
                'allowed': False,
                'tournament': DEFAULT_TOURNAMENT,
                'tournament_category': 'OTHER',
                'auto_catch_enabled': False,
                'auto_catch_channels': {}
            }

        # Ensure backward compatibility
        if 'season' in self.guilds[guild_id] and 'tournament' not in self.guilds[guild_id]:
            season_num = self.guilds[guild_id].get('season', '1')
            self.guilds[guild_id]['tournament'] = f"BOTS S{season_num}"
            del self.guilds[guild_id]['season']

        if 'tournament' not in self.guilds[guild_id]:
            self.guilds[guild_id]['tournament'] = DEFAULT_TOURNAMENT

        if 'tournament_category' not in self.guilds[guild_id]:
            self.guilds[guild_id]['tournament_category'] = 'OTHER'

        if 'auto_catch_enabled' not in self.guilds[guild_id]:
            self.guilds[guild_id]['auto_catch_enabled'] = False
        if 'auto_catch_channels' not in self.guilds[guild_id]:
            self.guilds[guild_id]['auto_catch_channels'] = {}

        if guild_id not in self.stats:
            self.stats[guild_id] = {}
        self.save_data()

    def is_auto_catch_enabled(self, guild_id: str, channel_id: str = None) -> bool:
        """
        Check if auto-catch is enabled for a guild/channel

        BOTH server AND channel must be enabled for auto-catch to work

        Args:
            guild_id: Discord guild ID as string
            channel_id: Discord channel ID as string (optional)

        Returns:
            True if auto-catch is enabled, False otherwise
        """
        self.init_guild(guild_id)

        server_enabled = self.guilds[guild_id].get('auto_catch_enabled', False)
        if not server_enabled:
            return False

        if channel_id is None:
            return True

        auto_catch_channels = self.guilds[guild_id].get('auto_catch_channels', {})

        if channel_id not in auto_catch_channels:
            return False

        return auto_catch_channels[channel_id]

    def set_auto_catch_server(self, guild_id: str, enabled: bool):
        """
        Enable or disable auto-catch for entire server

        Args:
            guild_id: Discord guild ID as string
            enabled: True to enable, False to disable
        """
        self.init_guild(guild_id)
        self.guilds[guild_id]['auto_catch_enabled'] = enabled
        self.save_data()

    def set_auto_catch_channel(self, guild_id: str, channel_id: str, enabled: bool):
        """
        Enable or disable auto-catch for specific channel

        Args:
            guild_id: Discord guild ID as string
            channel_id: Discord channel ID as string
            enabled: True to enable, False to disable
        """
        self.init_guild(guild_id)

        if 'auto_catch_channels' not in self.guilds[guild_id]:
            self.guilds[guild_id]['auto_catch_channels'] = {}

        self.guilds[guild_id]['auto_catch_channels'][channel_id] = enabled
        self.save_data()

    def get_enabled_channels(self, guild_id: str) -> list:
        """
        Get list of enabled channels for a guild

        Args:
            guild_id: Discord guild ID as string

        Returns:
            List of enabled channel IDs
        """
        self.init_guild(guild_id)
        auto_catch_channels = self.guilds[guild_id].get('auto_catch_channels', {})
        return [ch_id for ch_id, enabled in auto_catch_channels.items() if enabled]

    def _init_user_stats(self) -> Dict:
        """
        Create a fresh stats dictionary for a new user

        Returns:
            Dictionary with all stat fields initialized to 0
        """
        return {
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

    def add_stats(self, guild_id: str, user_id: str, runs: int, balls_played: int,
                  runs_conceded: int, balls_bowled: int, wickets: int, not_out: int = 0):
        """
        Add match statistics for a player

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            runs: Runs scored in the match
            balls_played: Balls faced in the match
            runs_conceded: Runs given while bowling
            balls_bowled: Balls bowled in the match
            wickets: Wickets taken in the match
            not_out: 0 = player was dismissed, 1 = player was not out
        """
        self.init_guild(guild_id)

        if user_id not in self.stats[guild_id]:
            self.stats[guild_id][user_id] = self._init_user_stats()

        stats = self.stats[guild_id][user_id]

        if 'matches' not in stats:
            stats['matches'] = 0
        if 'not_outs' not in stats:
            stats['not_outs'] = 0

        stats['matches'] += 1

        if balls_played > 0:
            stats['innings_bat'] += 1
            stats['runs'] += runs
            stats['balls_played'] += balls_played

            if runs > stats['high_score']:
                stats['high_score'] = runs

            if not_out == 1:
                stats['not_outs'] += 1

            if not_out == 0:
                stats['dismissals'] += 1
                if runs == 0:
                    stats['ducks'] += 1

            if runs >= 100:
                stats['hundreds'] += 1
            elif runs >= 50:
                stats['fifties'] += 1

        if balls_bowled > 0:
            stats['innings_bowl'] += 1
            stats['runs_conceded'] += runs_conceded
            stats['balls_bowled'] += balls_bowled
            stats['wickets'] += wickets

            if wickets > stats['best_bowling']:
                stats['best_bowling'] = wickets

            if wickets >= 4:
                stats['four_fers'] += 1
            elif wickets >= 3:
                stats['three_fers'] += 1

        self.save_data()

    def add_stats_with_history(self, guild_id: str, players_stats: List[Dict]):
        """
        Add match statistics WITH match history tracking

        Args:
            guild_id: Discord guild ID
            players_stats: List of player stat dictionaries from parsed data
        """
        from core.match_history import match_history
        from datetime import datetime

        match_id = f"{guild_id}_{int(datetime.now().timestamp())}"

        match_data = {
            'match_id': match_id,
            'timestamp': datetime.now().isoformat(),
            'players': players_stats
        }
        match_history.add_match(guild_id, match_data)

        for player_stat in players_stats:
            self.add_stats(
                guild_id,
                player_stat['user_id'],
                player_stat['runs'],
                player_stat['balls_played'],
                player_stat['runs_conceded'],
                player_stat['balls_bowled'],
                player_stat['wickets'],
                player_stat.get('not_out', 0)
            )

        return match_id

    def add_catch(self, guild_id: str, user_id: str, caught: bool):
        """
        Add fielding statistics for a player

        Args:
            guild_id: Discord guild ID
            user_id: Discord user ID
            caught: True if catch was taken, False if dropped
        """
        self.init_guild(guild_id)

        if user_id not in self.stats[guild_id]:
            self.stats[guild_id][user_id] = self._init_user_stats()

        if 'catches_taken' not in self.stats[guild_id][user_id]:
            self.stats[guild_id][user_id]['catches_taken'] = 0
        if 'catches_dropped' not in self.stats[guild_id][user_id]:
            self.stats[guild_id][user_id]['catches_dropped'] = 0

        if caught:
            self.stats[guild_id][user_id]['catches_taken'] += 1
        else:
            self.stats[guild_id][user_id]['catches_dropped'] += 1

        self.save_data()

    def set_maintenance_mode(self, enabled: bool):
        """
        Enable or disable maintenance mode

        Args:
            enabled: True to enable maintenance, False to disable
        """
        self.maintenance_mode = enabled
        self.save_data()

    def is_maintenance_mode(self) -> bool:
        """
        Check if bot is in maintenance mode

        Returns:
            True if maintenance mode is active, False otherwise
        """
        return self.maintenance_mode

    # Tournament category methods

    def get_current_tournament_category(self, guild_id: str) -> str:
        """
        Get category for current tournament

        Args:
            guild_id: Discord guild ID

        Returns:
            Current tournament category
        """
        self.init_guild(guild_id)
        return self.guilds[guild_id].get('tournament_category', 'OTHER')

    def set_current_tournament_category(self, guild_id: str, category: str):
        """
        Set category for current tournament

        Args:
            guild_id: Discord guild ID
            category: New category name
        """
        self.init_guild(guild_id)
        self.guilds[guild_id]['tournament_category'] = category.upper()
        self.save_data()

    def load_tournament_archive(self, guild_id: str, tournament_name: str) -> Dict:
        """
        Load complete tournament archive data (including metadata)

        Args:
            guild_id: Discord guild ID
            tournament_name: Tournament name

        Returns:
            Complete archive data dictionary
        """
        try:
            file_path = self.get_tournament_file_path(guild_id, tournament_name)

            if not os.path.exists(file_path):
                return {}

            with open(file_path, 'r') as f:
                archive_data = json.load(f)
                return archive_data

        except Exception as e:
            print(f"❌ Error loading tournament archive: {e}")
            return {}

    def get_tournament_category(self, guild_id: str, tournament_name: str) -> str:
        """
        Get category for a specific archived tournament

        Args:
            guild_id: Discord guild ID
            tournament_name: Tournament name

        Returns:
            Category name or 'OTHER'
        """
        archive_data = self.load_tournament_archive(guild_id, tournament_name)
        return archive_data.get('category', 'OTHER')

    def set_tournament_category(self, guild_id: str, tournament_name: str, category: str) -> bool:
        """
        Manually set category for an archived tournament

        Args:
            guild_id: Discord guild ID
            tournament_name: Tournament name
            category: New category name

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.get_tournament_file_path(guild_id, tournament_name)

            if not os.path.exists(file_path):
                return False

            with open(file_path, 'r') as f:
                archive_data = json.load(f)

            archive_data['category'] = category.upper()

            with open(file_path, 'w') as f:
                json.dump(archive_data, f, indent=2)

            print(f"✅ Tournament '{tournament_name}' category updated to '{category}'")
            return True

        except Exception as e:
            print(f"❌ Error setting tournament category: {e}")
            return False

    def get_tournaments_by_category(self, guild_id: str, category: str) -> List[str]:
        """
        Get all archived tournaments in a specific category

        Args:
            guild_id: Discord guild ID
            category: Category name

        Returns:
            List of tournament names in that category
        """
        all_tournaments = self.get_tournament_list(guild_id)
        result = []

        category_upper = category.upper()

        for tournament_name in all_tournaments:
            tournament_category = self.get_tournament_category(guild_id, tournament_name)

            if tournament_category == category_upper:
                result.append(tournament_name)

        return result

    def get_combined_stats(self, guild_id: str, category: Optional[str] = None) -> Dict:
        """
        Combine stats from tournaments

        If category is None: Combines ALL archived tournaments + current tournament
        If category specified: Combines archived tournaments in that category + current (if category matches)

        Args:
            guild_id: Discord guild ID
            category: Category name (None = everything)

        Returns:
            Dictionary of combined stats {user_id: combined_stats}
        """
        combined_stats = {}

        if category is None:
            # NO CATEGORY = EVERYTHING (all archived + current)
            all_tournaments = self.get_tournament_list(guild_id)

            for tournament_name in all_tournaments:
                tournament_stats = self.load_tournament_stats(guild_id, tournament_name)

                for user_id, stats in tournament_stats.items():
                    if user_id not in combined_stats:
                        combined_stats[user_id] = self._init_user_stats()

                    self._merge_stats(combined_stats[user_id], stats)

            current_stats = self.stats.get(guild_id, {})
            for user_id, stats in current_stats.items():
                if user_id not in combined_stats:
                    combined_stats[user_id] = self._init_user_stats()

                self._merge_stats(combined_stats[user_id], stats)

        else:
            # SPECIFIC CATEGORY = Archived in category + current (if matches)
            category_upper = category.upper()
            tournaments = self.get_tournaments_by_category(guild_id, category_upper)

            for tournament_name in tournaments:
                tournament_stats = self.load_tournament_stats(guild_id, tournament_name)

                for user_id, stats in tournament_stats.items():
                    if user_id not in combined_stats:
                        combined_stats[user_id] = self._init_user_stats()

                    self._merge_stats(combined_stats[user_id], stats)

            # Add current tournament if category matches
            current_category = self.get_current_tournament_category(guild_id)
            if current_category == category_upper:
                current_stats = self.stats.get(guild_id, {})
                for user_id, stats in current_stats.items():
                    if user_id not in combined_stats:
                        combined_stats[user_id] = self._init_user_stats()

                    self._merge_stats(combined_stats[user_id], stats)

        return combined_stats

    def _merge_stats(self, target: Dict, source: Dict):
        """
        Merge source stats into target stats

        Args:
            target: Target stats dictionary (modified in place)
            source: Source stats dictionary
        """
        target['matches'] += source.get('matches', 0)
        target['innings_bat'] += source.get('innings_bat', 0)
        target['runs'] += source.get('runs', 0)
        target['balls_played'] += source.get('balls_played', 0)
        target['not_outs'] += source.get('not_outs', 0)
        target['dismissals'] += source.get('dismissals', 0)
        target['innings_bowl'] += source.get('innings_bowl', 0)
        target['runs_conceded'] += source.get('runs_conceded', 0)
        target['balls_bowled'] += source.get('balls_bowled', 0)
        target['wickets'] += source.get('wickets', 0)
        target['fifties'] += source.get('fifties', 0)
        target['hundreds'] += source.get('hundreds', 0)
        target['ducks'] += source.get('ducks', 0)
        target['three_fers'] += source.get('three_fers', 0)
        target['four_fers'] += source.get('four_fers', 0)
        target['catches_taken'] += source.get('catches_taken', 0)
        target['catches_dropped'] += source.get('catches_dropped', 0)

        # Update maximums (not sums)
        target['high_score'] = max(target['high_score'], source.get('high_score', 0))
        target['best_bowling'] = max(target['best_bowling'], source.get('best_bowling', 0))

    def get_available_categories(self, guild_id: str) -> List[str]:
        """
        Get list of all unique categories for this guild (archived only)
        Does NOT include current tournament category

        Args:
            guild_id: Discord guild ID

        Returns:
            List of unique category names from archived tournaments
        """
        all_tournaments = self.get_tournament_list(guild_id)
        categories = set()

        for tournament_name in all_tournaments:
            category = self.get_tournament_category(guild_id, tournament_name)
            categories.add(category)

        return sorted(list(categories))

# Global data store instance
data_store = DataStore()
