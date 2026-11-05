"""
Discord UI Components Module
Contains all interactive UI elements (Views, Buttons, Dropdowns)
"""

import discord
from discord.ui import Select, View, Button
from core.data_store import data_store
from utils.calculations import calculate_catch_percentage
from ui.embeds import create_leaderboard_embed, create_archived_leaderboard_embed, create_all_time_leaderboard_embed
from config import CATCH_BUTTON_TIMEOUT

# Catch logging ui

class CatchButtonView(View):
    """
    Interactive buttons for logging catch opportunities
    Allows admins to mark catches as taken or dropped
    """

    def __init__(self, guild_id: str, user_id: str, username: str, bot_owner_id: int):
        super().__init__(timeout=CATCH_BUTTON_TIMEOUT)
        self.guild_id = guild_id
        self.user_id = user_id
        self.username = username
        self.bot_owner_id = bot_owner_id
        self.responded = False

    @discord.ui.button(label="Caught", style=discord.ButtonStyle.success, emoji="✅")
    async def caught_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handler for 'Caught' button - logs successful catch"""
        if self.responded:
            await interaction.response.send_message("❌ This catch has already been logged!", ephemeral=True)
            return

        if interaction.user.id != self.bot_owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only admins can log catches!", ephemeral=True)
            return

        self.responded = True

        data_store.add_catch(self.guild_id, self.user_id, caught=True)

        stats = data_store.stats.get(self.guild_id, {}).get(self.user_id, {})
        catches_taken = stats.get('catches_taken', 0)
        catches_dropped = stats.get('catches_dropped', 0)
        catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)

        success_embed = discord.Embed(
            title="✅ CATCH TAKEN!",
            description=f"**{self.username}** took the catch!\n\n🧤 **Total Catches:** {catches_taken}\n📊 **Success Rate:** {catch_percentage}%",
            color=discord.Color.green()
        )
        success_embed.set_footer(text=f"Logged by {interaction.user.name}")

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=success_embed, view=self)

    @discord.ui.button(label="Dropped", style=discord.ButtonStyle.danger, emoji="❌")
    async def dropped_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handler for 'Dropped' button - logs dropped catch"""
        if self.responded:
            await interaction.response.send_message("❌ This catch has already been logged!", ephemeral=True)
            return

        if interaction.user.id != self.bot_owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only admins can log catches!", ephemeral=True)
            return

        self.responded = True

        data_store.add_catch(self.guild_id, self.user_id, caught=False)

        stats = data_store.stats.get(self.guild_id, {}).get(self.user_id, {})
        catches_taken = stats.get('catches_taken', 0)
        catches_dropped = stats.get('catches_dropped', 0)
        catch_percentage = calculate_catch_percentage(catches_taken, catches_dropped)

        fail_embed = discord.Embed(
            title="❌ CATCH DROPPED!",
            description=f"**{self.username}** dropped the catch!\n\n💔 **Total Drops:** {catches_dropped}\n📊 **Success Rate:** {catch_percentage}%",
            color=discord.Color.red()
        )
        fail_embed.set_footer(text=f"Logged by {interaction.user.name}")

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=fail_embed, view=self)

# Leaderboard ui components (current)

class LeaderboardView(View):
    """View for leaderboard with timeout and interaction handling"""

    def __init__(self, guild_id: str, category: str, page: int):
        super().__init__(timeout=100)
        self.guild_id = guild_id
        self.category = category
        self.page = page
        self.message = None
        self.original_user = None

        self.add_item(LeaderboardDropdown(guild_id))
        self.add_item(LeaderboardPrevButton(guild_id, category, page))
        self.add_item(LeaderboardNextButton(guild_id, category, page))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command user can interact"""
        if self.original_user and interaction.user != self.original_user:
            await interaction.response.send_message(
                "❌ Only the person who called this leaderboard can interact with it!",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class LeaderboardDropdown(Select):
    """Dropdown menu for selecting leaderboard categories"""

    def __init__(self, guild_id: str):
        self.guild_id = guild_id

        options = [
            discord.SelectOption(label="Matches", emoji="🏏", value="matches"),
            discord.SelectOption(label="Runs", emoji="💥", value="runs"),
            discord.SelectOption(label="Wickets", emoji="🔥", value="wickets"),
            discord.SelectOption(label="Fantasy", emoji="✨", value="fantasy"),
            discord.SelectOption(label="Strike Rate", emoji="🚀", value="strike_rate"),
            discord.SelectOption(label="Catches Taken", emoji="🧤", value="catches_taken"),
            discord.SelectOption(label="Catches Dropped", emoji="💔", value="catches_dropped"),
            discord.SelectOption(label="Catch Success Rate", emoji="📊", value="catch_success"),
            discord.SelectOption(label="Batting Average", emoji="📈", value="bat_avg"),
            discord.SelectOption(label="Bowling Average", emoji="🎯", value="bowl_avg"),
            discord.SelectOption(label="High Score", emoji="🏆", value="high_score"),
            discord.SelectOption(label="Best Bowling", emoji="🎳", value="most_wickets"),
            discord.SelectOption(label="100s", emoji="💯", value="hundreds"),
            discord.SelectOption(label="50s", emoji="⭐", value="fifties"),
            discord.SelectOption(label="3-Fers", emoji="🥉", value="three_fers"),
            discord.SelectOption(label="4-Fers", emoji="🥇", value="four_fers"),
            discord.SelectOption(label="Ducks", emoji="🦆", value="ducks"),
            discord.SelectOption(label="Runs Conceded", emoji="🏃", value="runs_conceded"),
            discord.SelectOption(label="Balls Bowled", emoji="⚾", value="balls_bowled"),
            discord.SelectOption(label="Balls Played", emoji="⚽", value="balls_played")
        ]

        super().__init__(placeholder="Select leaderboard category...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        category = self.values[0]
        page = 0
        embed = create_leaderboard_embed(self.guild_id, category, page, interaction.guild)

        view = LeaderboardView(self.guild_id, category, page)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)


class LeaderboardPrevButton(Button):
    """Previous page button for leaderboard pagination"""

    def __init__(self, guild_id: str, category: str, page: int):
        self.guild_id = guild_id
        self.category = category
        self.page = page
        super().__init__(label="◀ Previous", style=discord.ButtonStyle.gray, disabled=(page == 0))

    async def callback(self, interaction: discord.Interaction):
        """Go to previous page"""
        new_page = max(0, self.page - 1)
        embed = create_leaderboard_embed(self.guild_id, self.category, new_page, interaction.guild)

        view = LeaderboardView(self.guild_id, self.category, new_page)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)


class LeaderboardNextButton(Button):
    """Next page button for leaderboard pagination"""

    def __init__(self, guild_id: str, category: str, page: int):
        self.guild_id = guild_id
        self.category = category
        self.page = page

        from ui.embeds import get_qualified_players_count
        qualified_count = get_qualified_players_count(guild_id, category)
        max_pages = (qualified_count - 1) // 9 if qualified_count > 0 else 0

        super().__init__(
            label="Next ▶",
            style=discord.ButtonStyle.primary,
            disabled=(page >= max_pages)
        )

    async def callback(self, interaction: discord.Interaction):
        """Go to next page"""
        from ui.embeds import get_qualified_players_count

        qualified_count = get_qualified_players_count(self.guild_id, self.category)
        max_pages = (qualified_count - 1) // 9 if qualified_count > 0 else 0
        new_page = min(max_pages, self.page + 1)

        embed = create_leaderboard_embed(self.guild_id, self.category, new_page, interaction.guild)

        view = LeaderboardView(self.guild_id, self.category, new_page)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)

# Archived leaderboard ui components

class ArchivedLeaderboardView(View):
    """View for archived tournament leaderboard"""

    def __init__(self, guild_id: str, tournament_name: str, category: str, page: int):
        super().__init__(timeout=100)
        self.guild_id = guild_id
        self.tournament_name = tournament_name
        self.category = category
        self.page = page
        self.message = None
        self.original_user = None

        self.add_item(ArchivedLeaderboardDropdown(guild_id, tournament_name))
        self.add_item(ArchivedLeaderboardPrevButton(guild_id, tournament_name, category, page))
        self.add_item(ArchivedLeaderboardNextButton(guild_id, tournament_name, category, page))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command user can interact"""
        if self.original_user and interaction.user != self.original_user:
            await interaction.response.send_message(
                "❌ Only the person who called this leaderboard can interact with it!",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class ArchivedLeaderboardDropdown(Select):
    """Dropdown for archived tournament leaderboard categories"""

    def __init__(self, guild_id: str, tournament_name: str):
        self.guild_id = guild_id
        self.tournament_name = tournament_name

        options = [
            discord.SelectOption(label="Matches", emoji="🏏", value="matches"),
            discord.SelectOption(label="Runs", emoji="💥", value="runs"),
            discord.SelectOption(label="Wickets", emoji="🔥", value="wickets"),
            discord.SelectOption(label="Fantasy", emoji="✨", value="fantasy"),
            discord.SelectOption(label="Strike Rate", emoji="🚀", value="strike_rate"),
            discord.SelectOption(label="Catches Taken", emoji="🧤", value="catches_taken"),
            discord.SelectOption(label="Catches Dropped", emoji="💔", value="catches_dropped"),
            discord.SelectOption(label="Catch Success Rate", emoji="📊", value="catch_success"),
            discord.SelectOption(label="Batting Average", emoji="📈", value="bat_avg"),
            discord.SelectOption(label="High Score", emoji="🏆", value="high_score"),
            discord.SelectOption(label="Best Bowling", emoji="🎳", value="most_wickets"),
            discord.SelectOption(label="100s", emoji="💯", value="hundreds"),
            discord.SelectOption(label="50s", emoji="⭐", value="fifties"),
            discord.SelectOption(label="3-Fers", emoji="🥉", value="three_fers"),
            discord.SelectOption(label="4-Fers", emoji="🥇", value="four_fers"),
            discord.SelectOption(label="Ducks", emoji="🦆", value="ducks"),
            discord.SelectOption(label="Runs Conceded", emoji="🏃", value="runs_conceded"),
            discord.SelectOption(label="Balls Bowled", emoji="⚾", value="balls_bowled"),
            discord.SelectOption(label="Balls Played", emoji="⚽", value="balls_played")
        ]

        super().__init__(placeholder="Select leaderboard category...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        category = self.values[0]
        page = 0
        embed = create_archived_leaderboard_embed(self.guild_id, self.tournament_name, category, page, interaction.guild)

        view = ArchivedLeaderboardView(self.guild_id, self.tournament_name, category, page)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)


class ArchivedLeaderboardPrevButton(Button):
    """Previous page button for archived leaderboard"""

    def __init__(self, guild_id: str, tournament_name: str, category: str, page: int):
        self.guild_id = guild_id
        self.tournament_name = tournament_name
        self.category = category
        self.page = page
        super().__init__(label="◀ Previous", style=discord.ButtonStyle.gray, disabled=(page == 0))

    async def callback(self, interaction: discord.Interaction):
        """Go to previous page"""
        new_page = max(0, self.page - 1)
        embed = create_archived_leaderboard_embed(self.guild_id, self.tournament_name, self.category, new_page, interaction.guild)

        view = ArchivedLeaderboardView(self.guild_id, self.tournament_name, self.category, new_page)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)


class ArchivedLeaderboardNextButton(Button):
    """Next page button for archived leaderboard"""

    def __init__(self, guild_id: str, tournament_name: str, category: str, page: int):
        self.guild_id = guild_id
        self.tournament_name = tournament_name
        self.category = category
        self.page = page

        from ui.embeds import get_qualified_players_count
        archived_stats = data_store.load_tournament_stats(guild_id, tournament_name)
        qualified_count = get_qualified_players_count(guild_id, category, archived_stats)
        max_pages = (qualified_count - 1) // 9 if qualified_count > 0 else 0

        super().__init__(
            label="Next ▶",
            style=discord.ButtonStyle.primary,
            disabled=(page >= max_pages)
        )

    async def callback(self, interaction: discord.Interaction):
        """Go to next page"""
        from ui.embeds import get_qualified_players_count

        archived_stats = data_store.load_tournament_stats(self.guild_id, self.tournament_name)
        qualified_count = get_qualified_players_count(self.guild_id, self.category, archived_stats)
        max_pages = (qualified_count - 1) // 9 if qualified_count > 0 else 0
        new_page = min(max_pages, self.page + 1)

        embed = create_archived_leaderboard_embed(self.guild_id, self.tournament_name, self.category, new_page, interaction.guild)

        view = ArchivedLeaderboardView(self.guild_id, self.tournament_name, self.category, new_page)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)

# Channel status ui

class ChannelStatusPrevButton(Button):
    """Previous page button for channel status"""

    def __init__(self, guild_id: str, page: int):
        self.guild_id = guild_id
        self.page = page
        super().__init__(label="◀", style=discord.ButtonStyle.gray, disabled=(page == 0))

    async def callback(self, interaction: discord.Interaction):
        """Go to previous page"""
        from ui.embeds import create_channel_status_embed
        new_page = max(0, self.page - 1)
        embed = create_channel_status_embed(self.guild_id, new_page, interaction.guild)

        view = View()

        stats = data_store.guilds.get(self.guild_id, {})
        auto_catch_channels = stats.get('auto_catch_channels', {})
        enabled_channels = [ch_id for ch_id, enabled in auto_catch_channels.items() if enabled]
        total_pages = (len(enabled_channels) - 1) // 10 + 1 if enabled_channels else 1

        if total_pages > 1:
            view.add_item(ChannelStatusPrevButton(self.guild_id, new_page))
            view.add_item(ChannelStatusNextButton(self.guild_id, new_page))

        await interaction.response.edit_message(embed=embed, view=view)

class ChannelStatusNextButton(Button):
    """Next page button for channel status"""

    def __init__(self, guild_id: str, page: int):
        self.guild_id = guild_id
        self.page = page

        stats = data_store.guilds.get(guild_id, {})
        auto_catch_channels = stats.get('auto_catch_channels', {})
        enabled_channels = [ch_id for ch_id, enabled in auto_catch_channels.items() if enabled]
        max_pages = (len(enabled_channels) - 1) // 10 if enabled_channels else 0

        super().__init__(
            label="▶",
            style=discord.ButtonStyle.primary,
            disabled=(page >= max_pages)
        )

    async def callback(self, interaction: discord.Interaction):
        """Go to next page"""
        from ui.embeds import create_channel_status_embed

        stats = data_store.guilds.get(self.guild_id, {})
        auto_catch_channels = stats.get('auto_catch_channels', {})
        enabled_channels = [ch_id for ch_id, enabled in auto_catch_channels.items() if enabled]
        max_pages = (len(enabled_channels) - 1) // 10 if enabled_channels else 0
        new_page = min(max_pages, self.page + 1)

        embed = create_channel_status_embed(self.guild_id, new_page, interaction.guild)

        view = View()

        total_pages = max_pages + 1
        if total_pages > 1:
            view.add_item(ChannelStatusPrevButton(self.guild_id, new_page))
            view.add_item(ChannelStatusNextButton(self.guild_id, new_page))

        await interaction.response.edit_message(embed=embed, view=view)

# Help command ui

class AdminHelpView(discord.ui.View):
    """Interactive view for help command with admin page toggle"""

    def __init__(self, basic_embed, admin_embed, original_user):
        super().__init__(timeout=180)
        self.basic_embed = basic_embed
        self.admin_embed = admin_embed
        self.original_user = original_user

        self.show_admin_button()

    def show_admin_button(self):
        """Clears buttons and shows only the 'Admin Commands' button"""
        self.clear_items()
        btn = Button(label="Admin Commands", style=discord.ButtonStyle.red, custom_id="admin_btn")
        btn.callback = self.admin_button_callback
        self.add_item(btn)

    def show_back_button(self):
        """Clears buttons and shows only the 'Back' button"""
        self.clear_items()
        btn = Button(label="Back", style=discord.ButtonStyle.green, custom_id="back_btn")
        btn.callback = self.back_button_callback
        self.add_item(btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the person who typed +help can click buttons"""
        if interaction.user != self.original_user:
            await interaction.response.send_message("Only the command sender can use these buttons.", ephemeral=True)
            return False
        return True

    async def admin_button_callback(self, interaction: discord.Interaction):
        """Switch to Admin Embed"""
        self.show_back_button()
        await interaction.response.edit_message(embed=self.admin_embed, view=self)

    async def back_button_callback(self, interaction: discord.Interaction):
        """Switch to Basic Embed"""
        self.show_admin_button()
        await interaction.response.edit_message(embed=self.basic_embed, view=self)

# Stats view with dropdown

class StatsView(View):
    """View for player stats with dropdown to switch between overall and recent"""

    def __init__(self, guild_id: str, user_id: str, guild, original_user):
        super().__init__(timeout=100)
        self.guild_id = guild_id
        self.user_id = user_id
        self.guild = guild
        self.original_user = original_user
        self.message = None
        self.current_view = "overall"
        self.recent_page = 0

        self.add_item(StatsDropdown(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command user can interact"""
        if interaction.user != self.original_user:
            await interaction.response.send_message(
                "❌ Only the person who called this command can interact with it!",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Disable all components when view times out"""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class StatsDropdown(Select):
    """Dropdown for switching between overall stats and recent performances"""

    def __init__(self, parent_view):
        self.parent_view = parent_view

        options = [
            discord.SelectOption(
                label="Overall Stats",
                emoji="📊",
                value="overall",
                description="View complete career statistics"
            ),
            discord.SelectOption(
                label="Recent Performances",
                emoji="📋",
                value="recent",
                description="View last few matches"
            )
        ]

        super().__init__(
            placeholder="Select view...",
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        selected = self.values[0]

        if selected == "overall":
            from ui.embeds import create_stats_embed
            embed = create_stats_embed(
                self.parent_view.user_id,
                self.parent_view.guild_id,
                self.parent_view.guild
            )

            view = StatsView(
                self.parent_view.guild_id,
                self.parent_view.user_id,
                self.parent_view.guild,
                self.parent_view.original_user
            )
            view.message = interaction.message

            await interaction.response.edit_message(embed=embed, view=view)

        elif selected == "recent":
            from ui.embeds import create_recent_performances_embed
            embed = create_recent_performances_embed(
                self.parent_view.user_id,
                self.parent_view.guild_id,
                self.parent_view.guild,
                page=0
            )

            view = RecentPerformancesView(
                self.parent_view.guild_id,
                self.parent_view.user_id,
                self.parent_view.guild,
                self.parent_view.original_user,
                page=0
            )
            view.message = interaction.message

            await interaction.response.edit_message(embed=embed, view=view)


class RecentPerformancesView(View):
    """View for recent performances with pagination"""

    def __init__(self, guild_id: str, user_id: str, guild, original_user, page: int):
        super().__init__(timeout=100)
        self.guild_id = guild_id
        self.user_id = user_id
        self.guild = guild
        self.original_user = original_user
        self.page = page
        self.message = None

        self.add_item(RecentPerformancesDropdown(self))

        from core.match_history import match_history
        player_matches = match_history.get_player_matches(guild_id, user_id)
        total_pages = (len(player_matches) - 1) // 5 + 1 if player_matches else 1

        if total_pages > 1:
            self.add_item(RecentPrevButton(self, page))
            self.add_item(RecentNextButton(self, page, total_pages))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command user can interact"""
        if interaction.user != self.original_user:
            await interaction.response.send_message(
                "❌ Only the person who called this command can interact with it!",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Disable all components when view times out"""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class RecentPerformancesDropdown(Select):
    """Dropdown for recent performances view"""

    def __init__(self, parent_view):
        self.parent_view = parent_view

        options = [
            discord.SelectOption(
                label="Overall Stats",
                emoji="📊",
                value="overall",
                description="View complete career statistics"
            ),
            discord.SelectOption(
                label="Recent Performances",
                emoji="📋",
                value="recent",
                description="View last few matches",
                default=True
            )
        ]

        super().__init__(
            placeholder="Select view...",
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        selected = self.values[0]

        if selected == "overall":
            from ui.embeds import create_stats_embed
            embed = create_stats_embed(
                self.parent_view.user_id,
                self.parent_view.guild_id,
                self.parent_view.guild
            )

            view = StatsView(
                self.parent_view.guild_id,
                self.parent_view.user_id,
                self.parent_view.guild,
                self.parent_view.original_user
            )
            view.message = interaction.message

            await interaction.response.edit_message(embed=embed, view=view)


class RecentPrevButton(Button):
    """Previous page button for recent performances"""

    def __init__(self, parent_view, page: int):
        self.parent_view = parent_view
        self.page = page
        super().__init__(
            label="◀",
            style=discord.ButtonStyle.gray,
            disabled=(page == 0),
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Go to previous page"""
        from ui.embeds import create_recent_performances_embed

        new_page = max(0, self.page - 1)
        embed = create_recent_performances_embed(
            self.parent_view.user_id,
            self.parent_view.guild_id,
            self.parent_view.guild,
            page=new_page
        )

        view = RecentPerformancesView(
            self.parent_view.guild_id,
            self.parent_view.user_id,
            self.parent_view.guild,
            self.parent_view.original_user,
            page=new_page
        )
        view.message = interaction.message

        await interaction.response.edit_message(embed=embed, view=view)


class RecentNextButton(Button):
    """Next page button for recent performances"""

    def __init__(self, parent_view, page: int, total_pages: int):
        self.parent_view = parent_view
        self.page = page
        super().__init__(
            label="▶",
            style=discord.ButtonStyle.primary,
            disabled=(page >= total_pages - 1),
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Go to next page"""
        from ui.embeds import create_recent_performances_embed
        from core.match_history import match_history

        player_matches = match_history.get_player_matches(
            self.parent_view.guild_id,
            self.parent_view.user_id
        )
        total_pages = (len(player_matches) - 1) // 5 + 1 if player_matches else 1

        new_page = min(total_pages - 1, self.page + 1)
        embed = create_recent_performances_embed(
            self.parent_view.user_id,
            self.parent_view.guild_id,
            self.parent_view.guild,
            page=new_page
        )

        view = RecentPerformancesView(
            self.parent_view.guild_id,
            self.parent_view.user_id,
            self.parent_view.guild,
            self.parent_view.original_user,
            page=new_page
        )
        view.message = interaction.message

        await interaction.response.edit_message(embed=embed, view=view)


class AllTimeLeaderboardView(View):
    """View for all-time leaderboard with category filtering"""

    def __init__(self, guild_id: str, category: str, leaderboard_category: str, page: int, is_all_time: bool = False):
        super().__init__(timeout=100)
        self.guild_id = guild_id
        self.category = category
        self.leaderboard_category = leaderboard_category
        self.page = page
        self.is_all_time = is_all_time  # True if showing all categories
        self.message = None
        self.original_user = None

        self.add_item(AllTimeLeaderboardDropdown(guild_id, category, is_all_time))
        self.add_item(AllTimeLeaderboardPrevButton(guild_id, category, leaderboard_category, page, is_all_time))
        self.add_item(AllTimeLeaderboardNextButton(guild_id, category, leaderboard_category, page, is_all_time))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command user can interact"""
        if self.original_user and interaction.user != self.original_user:
            await interaction.response.send_message(
                "❌ Only the person who called this leaderboard can interact with it!",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class AllTimeLeaderboardDropdown(Select):
    """Dropdown for all-time leaderboard categories"""

    def __init__(self, guild_id: str, category: str, is_all_time: bool = False):
        self.guild_id = guild_id
        self.category = category
        self.is_all_time = is_all_time

        options = [
            discord.SelectOption(label="Matches", emoji="🏏", value="matches"),
            discord.SelectOption(label="Runs", emoji="💥", value="runs"),
            discord.SelectOption(label="Wickets", emoji="🔥", value="wickets"),
            discord.SelectOption(label="Fantasy", emoji="✨", value="fantasy"),
            discord.SelectOption(label="Strike Rate", emoji="🚀", value="strike_rate"),
            discord.SelectOption(label="Catches Taken", emoji="🧤", value="catches_taken"),
            discord.SelectOption(label="Catches Dropped", emoji="💔", value="catches_dropped"),
            discord.SelectOption(label="Catch Success Rate", emoji="📊", value="catch_success"),
            discord.SelectOption(label="Batting Average", emoji="📈", value="bat_avg"),
            discord.SelectOption(label="High Score", emoji="🏆", value="high_score"),
            discord.SelectOption(label="Best Bowling", emoji="🎳", value="most_wickets"),
            discord.SelectOption(label="100s", emoji="💯", value="hundreds"),
            discord.SelectOption(label="50s", emoji="⭐", value="fifties"),
            discord.SelectOption(label="3-Fers", emoji="🥉", value="three_fers"),
            discord.SelectOption(label="4-Fers", emoji="🥇", value="four_fers"),
            discord.SelectOption(label="Ducks", emoji="🦆", value="ducks"),
            discord.SelectOption(label="Runs Conceded", emoji="🏃", value="runs_conceded"),
            discord.SelectOption(label="Balls Bowled", emoji="⚾", value="balls_bowled"),
            discord.SelectOption(label="Balls Played", emoji="⚽", value="balls_played")
        ]

        super().__init__(placeholder="Select leaderboard category...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        leaderboard_category = self.values[0]
        page = 0

        # Get combined stats (None if showing all-time)
        actual_category = None if self.is_all_time else self.category
        combined_stats = data_store.get_combined_stats(self.guild_id, actual_category)

        if self.is_all_time:
            all_tournaments = data_store.get_tournament_list(self.guild_id)
            tournament_count = len(all_tournaments)
        else:
            tournaments = data_store.get_tournaments_by_category(self.guild_id, self.category)
            tournament_count = len(tournaments)

        embed = create_all_time_leaderboard_embed(
            self.guild_id,
            self.category,
            combined_stats,
            tournament_count,
            leaderboard_category,
            page,
            interaction.guild
        )

        view = AllTimeLeaderboardView(self.guild_id, self.category, leaderboard_category, page, self.is_all_time)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)


class AllTimeLeaderboardPrevButton(Button):
    """Previous page button for all-time leaderboard"""

    def __init__(self, guild_id: str, category: str, leaderboard_category: str, page: int, is_all_time: bool = False):
        self.guild_id = guild_id
        self.category = category
        self.leaderboard_category = leaderboard_category
        self.page = page
        self.is_all_time = is_all_time
        super().__init__(label="◀ Previous", style=discord.ButtonStyle.gray, disabled=(page == 0))

    async def callback(self, interaction: discord.Interaction):
        """Go to previous page"""
        new_page = max(0, self.page - 1)

        actual_category = None if self.is_all_time else self.category
        combined_stats = data_store.get_combined_stats(self.guild_id, actual_category)

        if self.is_all_time:
            all_tournaments = data_store.get_tournament_list(self.guild_id)
            tournament_count = len(all_tournaments)
        else:
            tournaments = data_store.get_tournaments_by_category(self.guild_id, self.category)
            tournament_count = len(tournaments)

        embed = create_all_time_leaderboard_embed(
            self.guild_id,
            self.category,
            combined_stats,
            tournament_count,
            self.leaderboard_category,
            new_page,
            interaction.guild
        )

        view = AllTimeLeaderboardView(self.guild_id, self.category, self.leaderboard_category, new_page, self.is_all_time)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)


class AllTimeLeaderboardNextButton(Button):
    """Next page button for all-time leaderboard"""

    def __init__(self, guild_id: str, category: str, leaderboard_category: str, page: int, is_all_time: bool = False):
        self.guild_id = guild_id
        self.category = category
        self.leaderboard_category = leaderboard_category
        self.page = page
        self.is_all_time = is_all_time

        actual_category = None if is_all_time else category
        combined_stats = data_store.get_combined_stats(guild_id, actual_category)
        # Simple count for now (will be filtered in embed creation)
        max_pages = (len(combined_stats) - 1) // 9 if combined_stats else 0

        super().__init__(
            label="Next ▶",
            style=discord.ButtonStyle.primary,
            disabled=(page >= max_pages)
        )

    async def callback(self, interaction: discord.Interaction):
        """Go to next page"""
        actual_category = None if self.is_all_time else self.category
        combined_stats = data_store.get_combined_stats(self.guild_id, actual_category)

        if self.is_all_time:
            all_tournaments = data_store.get_tournament_list(self.guild_id)
            tournament_count = len(all_tournaments)
        else:
            tournaments = data_store.get_tournaments_by_category(self.guild_id, self.category)
            tournament_count = len(tournaments)

        # Calculate max pages (simple for now)
        max_pages = (len(combined_stats) - 1) // 9 if combined_stats else 0
        new_page = min(max_pages, self.page + 1)

        embed = create_all_time_leaderboard_embed(
            self.guild_id,
            self.category,
            combined_stats,
            tournament_count,
            self.leaderboard_category,
            new_page,
            interaction.guild
        )

        view = AllTimeLeaderboardView(self.guild_id, self.category, self.leaderboard_category, new_page, self.is_all_time)
        view.message = interaction.message
        view.original_user = interaction.user

        await interaction.response.edit_message(embed=embed, view=view)
