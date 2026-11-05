"""
All-Time Statistics Commands Module
Handles all-time stats viewing across tournament categories
"""

import discord
from discord.ext import commands
from typing import Optional

def setup_all_time_commands(bot):
    """Setup function to register all-time commands"""

    from core.data_store import data_store
    from ui.embeds import create_all_time_stats_embed, create_all_time_leaderboard_embed

    # All-time stats command

    @bot.command(name='allstats', aliases=['ast'])
    async def all_time_stats(ctx, target: Optional[str] = None, category: Optional[str] = None):
        """
        View all-time stats across tournaments

        No category = All tournaments combined
        With category = Specific category only

        Usage:
            +allstats               - Your all-time stats (everything)
            +allstats @user         - User's all-time stats (everything)
            +allstats @user BPSL    - User's BPSL all-time stats
            +allstats BPSL          - Your BPSL all-time stats (if no user found)
        """
        guild_id = str(ctx.guild.id)

        user_id = None
        actual_category = None

        if target:
            # Check if it's a mention
            if ctx.message.mentions:
                user_id = str(ctx.message.mentions[0].id)
                # Category is the second parameter
                actual_category = category
            # Check if it's a user ID
            elif target.isdigit():
                user_id = target
                actual_category = category
            # Check if it's a username
            else:
                member = discord.utils.find(
                    lambda m: m.name.lower() == target.lower() or
                             m.display_name.lower() == target.lower(),
                    ctx.guild.members
                )
                if member:
                    user_id = str(member.id)
                    actual_category = category
                else:
                    # Not a user, must be a category
                    user_id = str(ctx.author.id)
                    actual_category = target
        else:
            # No target = command author
            user_id = str(ctx.author.id)

        # Get combined stats (None = everything, category = specific)
        combined_stats = data_store.get_combined_stats(guild_id, actual_category.upper() if actual_category else None)

        # Check if user has stats
        if user_id not in combined_stats:
            available_categories = data_store.get_available_categories(guild_id)

            category_display = f"**{actual_category.upper()}**" if actual_category else "any"

            embed = discord.Embed(
                title="❌ No Stats Found",
                description=f"No {category_display} all-time stats found for this player.",
                color=discord.Color.red()
            )

            if available_categories:
                embed.add_field(
                    name="Available Categories",
                    value="\n".join(f"• `{cat}`" for cat in available_categories),
                    inline=False
                )

            embed.set_footer(text="Try a different category or use +ashelp for usage examples")
            await ctx.send(embed=embed)
            return

        # Get tournament count (for display purposes)
        if actual_category:
            tournaments = data_store.get_tournaments_by_category(guild_id, actual_category.upper())
            tournament_count = len(tournaments)
        else:
            # All tournaments
            all_tournaments = data_store.get_tournament_list(guild_id)
            tournament_count = len(all_tournaments)

        user_stats = combined_stats[user_id]

        embed = create_all_time_stats_embed(
            user_id,
            user_stats,
            actual_category.upper() if actual_category else None,
            tournament_count,
            ctx.guild
        )

        await ctx.send(embed=embed)

    # All-time leaderboard command

    @bot.command(name='alllb', aliases=['allb'])
    async def all_time_leaderboard(ctx, category: Optional[str] = None):
        """
        All-time leaderboard

        No category = All tournaments combined
        With category = Specific category only

        Usage:
            +alllb          - All-time leaderboard (everything)
            +alllb BPSL     - BPSL all-time leaderboard
            +alllb BOTS     - BOTS all-time leaderboard
        """
        guild_id = str(ctx.guild.id)

        # Get combined stats (None = everything)
        combined_stats = data_store.get_combined_stats(guild_id, category.upper() if category else None)

        if not combined_stats:
            available_categories = data_store.get_available_categories(guild_id)

            category_display = f"**{category.upper()}**" if category else "any"

            embed = discord.Embed(
                title="❌ No Stats Found",
                description=f"No {category_display} all-time stats found.",
                color=discord.Color.red()
            )

            if available_categories:
                embed.add_field(
                    name="Available Categories",
                    value="\n".join(f"• `{cat}`" for cat in available_categories),
                    inline=False
                )

            await ctx.send(embed=embed)
            return

        # Get tournament count (for display, not critical)
        if category:
            tournaments = data_store.get_tournaments_by_category(guild_id, category.upper())
            tournament_count = len(tournaments)
            category_display = category.upper()
        else:
            all_tournaments = data_store.get_tournament_list(guild_id)
            tournament_count = len(all_tournaments)
            category_display = "All-Time"

        # Default to runs leaderboard
        leaderboard_category = 'runs'
        page = 0

        embed = create_all_time_leaderboard_embed(
            guild_id,
            category_display,
            combined_stats,
            tournament_count,
            leaderboard_category,
            page,
            ctx.guild
        )

        from ui.views import AllTimeLeaderboardView
        view = AllTimeLeaderboardView(guild_id, category_display, leaderboard_category, page, category is None)
        view.original_user = ctx.author
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # All-time stats help command

    @bot.command(name='ashelp')
    async def all_time_help(ctx):
        """
        Show help for all-time stats commands

        Usage:
            +ashelp
        """
        embed = discord.Embed(
            title="🏆 All-Time Stats Commands - Help",
            description="View combined statistics across multiple tournaments",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📊 View All-Time Stats",
            value=(
                "`+allstats` - Your all-time stats (everything combined)\n"
                "`+allstats BPSL` - Your BPSL category stats\n"
                "`+allstats @user` - User's all-time stats\n"
                "`+allstats @user BPSL` - User's BPSL stats\n"
            ),
            inline=False
        )

        embed.add_field(
            name="🏆 All-Time Leaderboards",
            value=(
                "`+alllb` - All-time leaderboard (BPSL + BOTS + all)\n"
                "`+alllb BPSL` - BPSL category leaderboard\n"
                "`+alllb BOTS` - BOTS category leaderboard"
            ),
            inline=False
        )

        embed.add_field(
            name="📂 Category Management",
            value=(
                "`+categories` - List all available categories\n"
                "`+setcategory <category>` - (Admin)\n"
                "`+categorize <name> <category>` - (Admin)"
            ),
            inline=False
        )


        embed.set_footer(text="Use `+help` for main bot commands")

        await ctx.send(embed=embed)

    # CATEGORIZE TOURNAMENT (Admin)

    @bot.command(name='categorize')
    async def categorize_tournament(ctx, tournament_name: str, category: str):
        """
        Manually set category for a tournament (Admin only)

        Useful for organizing existing archived tournaments

        Usage:
            +categorize BPSL1 BPSL
            +categorize "Old Tournament" OTHER
            +categorize BOTS19 BOTS
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        success = data_store.set_tournament_category(guild_id, tournament_name, category)

        if success:
            embed = discord.Embed(
                title="✅ Category Updated",
                description=f"**{tournament_name}** → Category: **{category.upper()}**",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Updated by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Tournament Not Found",
                description=f"Could not find tournament: **{tournament_name}**",
                color=discord.Color.red()
            )

            tournaments = data_store.get_tournament_list(guild_id)
            if tournaments:
                embed.add_field(
                    name="Available Tournaments",
                    value="\n".join(f"• `{t}`" for t in tournaments[:10]),
                    inline=False
                )
                if len(tournaments) > 10:
                    embed.set_footer(text=f"Showing 10 of {len(tournaments)} tournaments")

            await ctx.send(embed=embed)

    # LIST CATEGORIES (Utility)

    @bot.command(name='categories')
    async def list_categories(ctx):
        """
        Show all available tournament categories

        Usage:
            +categories
        """
        guild_id = str(ctx.guild.id)

        categories = data_store.get_available_categories(guild_id)

        if not categories:
            embed = discord.Embed(
                title="📋 Tournament Categories",
                description="No archived tournaments found yet!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="📋 Tournament Categories",
            description="Available categories for all-time stats:",
            color=discord.Color.blue()
        )

        for category in categories:
            tournaments = data_store.get_tournaments_by_category(guild_id, category)
            tournament_list = ", ".join(tournaments[:5])
            if len(tournaments) > 5:
                tournament_list += f" (+{len(tournaments) - 5} more)"

            embed.add_field(
                name=f"🏆 {category}",
                value=f"**{len(tournaments)} tournament(s)**\n{tournament_list}",
                inline=False
            )

        embed.add_field(
            name="📊 View All-Time Stats",
            value=(
                "• `+allstats BPSL` - Your BPSL all-time stats\n"
                "• `+alllb BPSL` - BPSL all-time leaderboard"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    # Error handlers
    @categorize_tournament.error
    async def categorize_error(ctx, error):
        """Handle permission errors gracefully"""
        if ctx.author.id == bot.owner_id:
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command!")
