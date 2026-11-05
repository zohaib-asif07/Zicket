"""
Leaderboard Commands Module
Handles server leaderboard display with interactive UI
"""


def setup_leaderboard_commands(bot):
    """Setup function to register leaderboard commands"""

    from ui.embeds import create_leaderboard_embed, create_archived_leaderboard_embed
    from ui.views import LeaderboardView, ArchivedLeaderboardView
    from core.data_store import data_store

    @bot.command(name='lb')
    async def leaderboard(ctx, tournament: str = None):
        """
        Show server leaderboard (current or archived tournament)

        Interactive leaderboard with dropdown to select category
        and buttons for pagination

        Usage:
            +lb              - Current tournament leaderboard
            +lb BOTS19       - Archived tournament leaderboard

        Categories:
        - Matches, Runs, Wickets, Fantasy Points
        - Strike Rate, Batting Average
        - High Score, Best Bowling
        - 50s, 100s, Ducks
        - 3-Fers, 4-Fers
        - Catches Taken/Dropped, Catch Success Rate
        - And more!
        """
        guild_id = str(ctx.guild.id)

        # Check if tournament parameter is provided
        if tournament:
            tournaments_list = data_store.get_tournament_list(guild_id)

            # If tournament doesn't exist, treat it as current tournament (ignore invalid name)
            if tournament not in tournaments_list:
                # Just show current leaderboard (ignore the invalid tournament name)
                category = 'runs'
                page = 0

                embed = create_leaderboard_embed(guild_id, category, page, ctx.guild)

                view = LeaderboardView(guild_id, category, page)
                view.original_user = ctx.author
                message = await ctx.send(embed=embed, view=view)
                view.message = message
                return

            category = 'runs'  # Default category
            page = 0

            embed = create_archived_leaderboard_embed(guild_id, tournament, category, page, ctx.guild)

            view = ArchivedLeaderboardView(guild_id, tournament, category, page)
            view.original_user = ctx.author
            message = await ctx.send(embed=embed, view=view)
            view.message = message
        else:
            category = 'runs'  # Default category
            page = 0

            embed = create_leaderboard_embed(guild_id, category, page, ctx.guild)

            view = LeaderboardView(guild_id, category, page)
            view.original_user = ctx.author
            message = await ctx.send(embed=embed, view=view)
            view.message = message
