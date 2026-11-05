"""
Team Management Commands Module
Handles team setup, match results, and points table display
"""

import discord
from discord.ui import Select, View, Button
import asyncio
from core.teams_store import teams_store
from utils.points_table_graphics import generate_points_table_graphic

def setup_team_management_commands(bot):
    """Setup function to register team management commands"""

    # Setup teams

    @bot.command(name='setup')
    async def setup_teams(ctx):
        """
        Setup teams for points table (Admin only)

        Interactive setup process for up to 5 teams

        Usage:
            +setup
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        # Check if teams already exist
        if teams_store.guild_has_teams(guild_id):
            embed = discord.Embed(
                title="⚠️ Teams Already Exist",
                description=(
                    "This server already has teams set up!\n\n"
                    "**To reset and start over:**\n"
                    "Use `+resetteams` first, then run `+setup` again."
                ),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        setup_embed = discord.Embed(
            title="🏆 Team Setup Wizard",
            description=(
                "Let's set up your league teams!\n\n"
                "**You can add up to 6 teams.**\n\n"
                "For each team, I'll ask for:\n"
                "1️⃣ Team Name (max 16 characters)\n"
                "2️⃣ Color (hex code like #FF5733)\n"
                "3️⃣ Logo (optional image upload)\n\n"
                "You have **60 seconds** for each step.\n"
                "Type `skip` to skip a team."
            ),
            color=discord.Color.blue()
        )
        setup_embed.set_footer(text="React with ✅ to start setup")

        msg = await ctx.send(embed=setup_embed)
        await msg.add_reaction('✅')

        def check_reaction(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅' and reaction.message.id == msg.id

        try:
            await bot.wait_for('reaction_add', timeout=60.0, check=check_reaction)
        except asyncio.TimeoutError:
            await ctx.send("❌ Setup cancelled (timeout)")
            return

        teams_data = {}

        def check_message(m):
            return m.author == ctx.author and m.channel == ctx.channel

        # Setup up to 5 teams
        for i in range(1, 7):
            await ctx.send(f"**Team {i}/5** - Enter team name (max 16 chars) or type `skip`:")

            try:
                name_msg = await bot.wait_for('message', timeout=60.0, check=check_message)
                team_name = name_msg.content.strip()

                if team_name.lower() == 'skip':
                    await ctx.send(f"⏭️ Skipped Team {i}")
                    continue

                # Limit to 16 characters
                team_name = team_name[:16]

            except asyncio.TimeoutError:
                await ctx.send(f"⏱️ Timeout! Using default name: `Team {i}`")
                team_name = f"Team {i}"

            # Ask for color (hex code)
            await ctx.send(f"**{team_name}** - Enter color hex code (e.g., #FF5733):")

            try:
                color_msg = await bot.wait_for('message', timeout=60.0, check=check_message)
                hex_color = color_msg.content.strip()

                if hex_color.startswith('#'):
                    hex_color = hex_color[1:]

                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                color = (r, g, b, 180)  # 180 alpha for slight transparency

            except (asyncio.TimeoutError, ValueError):
                await ctx.send("⏱️ Timeout or invalid color! Using default color.")
                # Default colors based on team number
                default_colors = [
                    (5, 255, 186, 180),    # Cyan
                    (217, 142, 3, 180),    # Orange
                    (0, 103, 182, 180),    # Blue
                    (175, 56, 255, 180),   # Purple
                    (206, 159, 237, 180),  # Light Purple
                    (255, 99, 71, 180),    # Tomato Red
                ]
                color = default_colors[i - 1]

            await ctx.send(f"**{team_name}** - Upload team logo image (or type `skip`):")

            logo_filename = None

            try:
                logo_msg = await bot.wait_for('message', timeout=60.0, check=check_message)

                if logo_msg.content.lower() == 'skip':
                    await ctx.send("Are you sure you don't want a logo? Reply `yes` to use default circle or `no` to upload:")
                    confirm_msg = await bot.wait_for('message', timeout=60.0, check=check_message)

                    if confirm_msg.content.lower() == 'yes':
                        logo_filename = 'default_logo.png'
                    else:
                        # Give 60 more seconds
                        await ctx.send("Upload logo now (60 seconds):")
                        logo_msg = await bot.wait_for('message', timeout=60.0, check=check_message)

                if logo_msg.attachments:
                    attachment = logo_msg.attachments[0]

                    logo_filename = f"{guild_id}_{team_name.replace(' ', '_').lower()}.png"
                    logo_path = teams_store.get_logo_path(logo_filename)

                    await attachment.save(logo_path)
                    await ctx.send("✅ Logo saved!")
                elif not logo_filename:
                    logo_filename = 'default_logo.png'

            except asyncio.TimeoutError:
                await ctx.send("⏱️ Timeout! Using default logo (white circle).")
                logo_filename = 'default_logo.png'

            teams_data[team_name] = {
                'color': list(color),  # Convert tuple to list for JSON
                'logo': logo_filename
            }

            await ctx.send(f"✅ **{team_name}** added!\n{'━' * 40}")

        if not teams_data:
            await ctx.send("❌ No teams were added. Setup cancelled.")
            return

        teams_store.init_guild_teams(guild_id, teams_data)

        success_embed = discord.Embed(
            title="✅ Setup Complete!",
            description=f"Successfully set up **{len(teams_data)} teams** for this league!\n\nUse `+pointstable` to view the table.",
            color=discord.Color.green()
        )
        success_embed.set_footer(text=f"Set up by {ctx.author.name}")
        await ctx.send(embed=success_embed)

    # Points table display

    @bot.command(name='pointstable', aliases=['pt'])
    async def points_table(ctx):
        """
        Display current points table

        Usage:
            +pointstable
            +pt
        """
        guild_id = str(ctx.guild.id)

        # Check if teams exist
        if not teams_store.guild_has_teams(guild_id):
            embed = discord.Embed(
                title="📋 No Data Entered",
                description=(
                    "No teams have been set up yet!\n\n"
                    "**To get started:**\n"
                    "Use `+setup` to create your league teams."
                ),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            teams = teams_store.get_teams_list(guild_id)

            image_binary = await generate_points_table_graphic(teams)

            await ctx.send(
                file=discord.File(fp=image_binary, filename='points_table.png')
            )

        except Exception as e:
            await ctx.send(f"❌ Error generating points table: {str(e)}")
            print(f"❌ Points table error: {e}")
            import traceback
            traceback.print_exc()

    # Match result

    @bot.command(name='matchresult', aliases=['mr'])
    async def match_result(ctx):
        """
        Record a match result (Admin only)

        Interactive dropdown to select teams and winner

        Usage:
            +matchresult
            +mr
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        # Check if teams exist
        if not teams_store.guild_has_teams(guild_id):
            await ctx.send("❌ No teams set up! Use `+setup` first.")
            return

        teams_dict = teams_store.get_teams(guild_id)
        team_names = list(teams_dict.keys())

        if len(team_names) < 2:
            await ctx.send("❌ You need at least 2 teams to record a match!")
            return

        view = MatchResultView(guild_id, team_names, ctx.author)

        embed = discord.Embed(
            title="🏏 Record Match Result",
            description="Select the two teams that played:",
            color=discord.Color.blue()
        )

        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # Reset teams

    @bot.command(name='resetteams')
    async def reset_teams(ctx):
        """
        Reset all teams and start fresh (Admin only)

        WARNING: This deletes all team data and match history!

        Usage:
            +resetteams
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        # Check if teams exist
        if not teams_store.guild_has_teams(guild_id):
            await ctx.send("⚠️ No teams to reset!")
            return

        await ctx.send("⚠️ **WARNING:** This will delete all teams and match history!\n\nType `yes` to confirm:")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
            if msg.content.lower() == 'yes':
                teams_store.reset_guild_teams(guild_id)
                await ctx.send("✅ All teams have been reset! Use `+setup` to create new teams.")
            else:
                await ctx.send("❌ Reset cancelled.")
        except asyncio.TimeoutError:
            await ctx.send("❌ Reset cancelled (timeout).")


# Match result view (ui)

class MatchResultView(View):
    """Interactive view for recording match results"""

    def __init__(self, guild_id: str, team_names: list, author):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.team_names = team_names
        self.author = author
        self.team1 = None
        self.team2 = None
        self.message = None

        self.add_item(TeamSelectDropdown(team_names, 1, self))
        self.add_item(TeamSelectDropdown(team_names, 2, self))

    async def on_timeout(self):
        """Disable all components when timeout"""
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class TeamSelectDropdown(Select):
    """Dropdown for selecting a team"""

    def __init__(self, team_names: list, team_number: int, parent_view):
        self.team_number = team_number
        self.parent_view = parent_view

        options = [
            discord.SelectOption(label=name, value=name)
            for name in team_names
        ]

        super().__init__(
            placeholder=f"Select Team {team_number}...",
            options=options,
            row=team_number - 1
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle team selection"""
        if interaction.user != self.parent_view.author:
            await interaction.response.send_message("❌ Only the command user can select teams!", ephemeral=True)
            return

        selected_team = self.values[0]

        if self.team_number == 1:
            self.parent_view.team1 = selected_team
        else:
            self.parent_view.team2 = selected_team

        # Check if both teams are selected
        if self.parent_view.team1 and self.parent_view.team2:
            # Check if same team selected twice
            if self.parent_view.team1 == self.parent_view.team2:
                await interaction.response.send_message("❌ You selected the same team twice! Please select different teams.", ephemeral=True)
                self.parent_view.team1 = None
                self.parent_view.team2 = None
                return

            await self.show_winner_selection(interaction)
        else:
            await interaction.response.send_message(f"✅ {selected_team} selected as Team {self.team_number}", ephemeral=True)

    async def show_winner_selection(self, interaction: discord.Interaction):
        """Show buttons to select winner"""
        embed = discord.Embed(
            title="🏏 Match Result",
            description=f"**{self.parent_view.team1}** vs **{self.parent_view.team2}**\n\nWho won?",
            color=discord.Color.gold()
        )

        view = WinnerSelectionView(
            self.parent_view.guild_id,
            self.parent_view.team1,
            self.parent_view.team2,
            self.parent_view.author
        )

        await interaction.response.edit_message(embed=embed, view=view)


class WinnerSelectionView(View):
    """View for selecting match winner"""

    def __init__(self, guild_id: str, team1: str, team2: str, author):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.team1 = team1
        self.team2 = team2
        self.author = author

        self.add_item(WinnerButton(team1, team2, guild_id, author, 1))
        self.add_item(WinnerButton(team2, team1, guild_id, author, 2))

    async def on_timeout(self):
        """Disable buttons on timeout"""
        for item in self.children:
            item.disabled = True


class WinnerButton(Button):
    """Button to select match winner"""

    def __init__(self, winner: str, loser: str, guild_id: str, author, button_num: int):
        self.winner = winner
        self.loser = loser
        self.guild_id = guild_id
        self.author_user = author

        super().__init__(
            label=winner,
            style=discord.ButtonStyle.green if button_num == 1 else discord.ButtonStyle.blurple,
            custom_id=f"winner_{button_num}"
        )

    async def callback(self, interaction: discord.Interaction):
        """Record match result"""
        if interaction.user != self.author_user:
            await interaction.response.send_message("❌ Only the command user can select the winner!", ephemeral=True)
            return

        success = teams_store.record_match_result(self.guild_id, self.winner, self.loser)

        if not success:
            await interaction.response.send_message("❌ Error recording match result!", ephemeral=True)
            return

        result_embed = discord.Embed(
            title="✅ Match Result Recorded!",
            description=f"**{self.winner}** defeated **{self.loser}**",
            color=discord.Color.green()
        )

        teams_dict = teams_store.get_teams(self.guild_id)
        winner_stats = teams_dict[self.winner]
        loser_stats = teams_dict[self.loser]

        result_embed.add_field(
            name=f"🏆 {self.winner}",
            value=f"P: {winner_stats['played']} | W: {winner_stats['won']} | L: {winner_stats['lost']} | Pts: {winner_stats['points']}",
            inline=False
        )

        result_embed.add_field(
            name=f"📉 {self.loser}",
            value=f"P: {loser_stats['played']} | W: {loser_stats['won']} | L: {loser_stats['lost']} | Pts: {loser_stats['points']}",
            inline=False
        )

        result_embed.set_footer(text=f"Recorded by {interaction.user.name}")

        for item in self.view.children:
            item.disabled = True

        await interaction.response.edit_message(embed=result_embed, view=self.view)
