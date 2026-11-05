"""
Owner Commands Module
Bot owner exclusive commands for access control and data management
"""

import asyncio
import discord
from config import COMMAND_RESPONSE_TIMEOUT

def setup_owner_commands(bot):
    """Setup function to register owner commands"""

    from core.data_store import data_store

    # GRANT ACCESS (Owner Only)

    @bot.command(name='grantaccess')
    async def grant_access(ctx, guild_id: str):
        """
        Grant a server access to use the bot (Owner only)

        Usage:
            +grantaccess 123456789012345678
        """
        if ctx.author.id != bot.owner_id:
            await ctx.send(f"❌ Only the bot owner can use this command! (Your ID: {ctx.author.id})")
            return

        data_store.init_guild(guild_id)
        data_store.guilds[guild_id]['allowed'] = True
        data_store.save_data()

        await ctx.send(f"✅ Access granted to guild `{guild_id}`")

    # REVOKE ACCESS (Owner Only)

    @bot.command(name='revokeaccess')
    async def revoke_access(ctx, guild_id: str):
        """
        Revoke a server's access to the bot (Owner only)

        Usage:
            +revokeaccess 123456789012345678
        """
        if ctx.author.id != bot.owner_id:
            await ctx.send(f"❌ Only the bot owner can use this command! (Your ID: {ctx.author.id})")
            return

        if guild_id in data_store.guilds:
            data_store.guilds[guild_id]['allowed'] = False
            data_store.save_data()

        await ctx.send(f"✅ Access revoked from guild `{guild_id}`")

    # RESET GUILD WITH TOURNAMENT ARCHIVE (Owner Only)

    @bot.command(name='reset')
    async def reset_guild(ctx, guild_id: str):
        """
        Reset guild data and archive current tournament (Owner only)

        This will:
        1. Save current stats to a tournament archive file
        2. Add tournament to the archive list
        3. Clear current stats for fresh tournament

        WARNING: Current stats will be archived and cleared!

        Usage:
            +reset 123456789012345678
        """
        if ctx.author.id != bot.owner_id:
            await ctx.send(f"❌ Only the bot owner can use this command! (Your ID: {ctx.author.id})")
            return

        # Check if guild exists
        if guild_id not in data_store.guilds and guild_id not in data_store.stats:
            await ctx.send(f"❌ Guild `{guild_id}` has no data to reset!")
            return

        data_store.init_guild(guild_id)
        tournament_name = data_store.guilds[guild_id].get('tournament', '6PSL S1')

        confirm_embed = discord.Embed(
            title="⚠️ Confirm Tournament Archive & Reset",
            description=(
                f"**Current Tournament:** `{tournament_name}`\n\n"
                f"This action will:\n"
                f"1️⃣ Archive current stats to `{tournament_name.replace(' ', '')}.json`\n"
                f"2️⃣ Clear all current player statistics\n"
                f"3️⃣ Keep guild settings (prefix, channels, etc.)\n\n"
                f"**The archived tournament will be READ-ONLY.**\n\n"
                f"Type `yes` to confirm, or `no` to cancel."
            ),
            color=discord.Color.orange()
        )

        await ctx.send(embed=confirm_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=COMMAND_RESPONSE_TIMEOUT)

            if msg.content.lower() != 'yes':
                await ctx.send("❌ Reset cancelled.")
                return

            # Archive tournament
            success = data_store.archive_tournament(guild_id, tournament_name)

            if not success:
                error_embed = discord.Embed(
                    title="❌ Archive Failed",
                    description="Could not archive tournament. Reset cancelled.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return

            # Clear stats (but keep guild settings)
            if guild_id in data_store.stats:
                data_store.stats[guild_id] = {}

            # Clear match history
            from core.match_history import match_history
            if guild_id in match_history.matches:
                match_history.matches[guild_id] = []
                match_history.save_data()

            data_store.save_data()

            success_embed = discord.Embed(
                title="✅ Tournament Archived & Reset Complete",
                description=(
                    f"**Archived Tournament:** `{tournament_name}`\n"
                    f"**Archive File:** `{tournament_name.replace(' ', '')}.json`\n\n"
                    f"✅ All stats archived successfully\n"
                    f"✅ Current stats cleared\n"
                    f"✅ Guild settings preserved\n\n"
                    f"**Access archived stats with:**\n"
                    f"• `+stats @user {tournament_name.replace(' ', '')}`\n"
                    f"• `+lb {tournament_name.replace(' ', '')}`\n"
                    f"• `+tournamentlist` to see all archives"
                ),
                color=discord.Color.green()
            )

            await ctx.send(embed=success_embed)

        except asyncio.TimeoutError:
            await ctx.send("❌ Reset cancelled (timeout).")

    # TOURNAMENT LIST (Owner Only)

    @bot.command(name='tournamentlist', aliases=['tl'])
    async def tournament_list(ctx):
        """
        List all archived tournaments for current server

        Usage:
            +tournamentlist
            +tl
        """
        guild_id = str(ctx.guild.id)

        tournaments = data_store.get_tournament_list(guild_id)

        if not tournaments:
            embed = discord.Embed(
                title="📜 Tournament Archives",
                description=(
                    "No archived tournaments found for this server.\n\n"
                    "**To archive current tournament:**\n"
                    "Use `+reset <guild_id>` (Owner only)"
                ),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        data_store.init_guild(guild_id)
        current_tournament = data_store.guilds[guild_id].get('tournament', '6PSL S1')

        embed = discord.Embed(
            title="📜 Tournament Archives",
            description=f"**Current Tournament:** `{current_tournament}`\n\n**Archived Tournaments:**",
            color=discord.Color.blue()
        )

        # Add tournaments (max 25 fields)
        for idx, tournament in enumerate(tournaments[:25], 1):
            embed.add_field(
                name=f"{idx}. {tournament}",
                value=f"• `+stats @user {tournament}`\n• `+lb {tournament}`",
                inline=False
            )

        if len(tournaments) > 25:
            embed.set_footer(text=f"Showing 25 of {len(tournaments)} tournaments")
        else:
            embed.set_footer(text=f"Total: {len(tournaments)} archived tournament(s)")

        await ctx.send(embed=embed)

    # RESET BOT (Owner Only)

    @bot.command(name='resetbot')
    async def reset_bot(ctx):
        """
        Reset ALL bot data (Owner only)

        WARNING: This deletes EVERYTHING - all guilds and all statistics!
        Requires confirmation.

        Usage:
            +resetbot
            (Then type 'yes' to confirm)
        """
        if ctx.author.id != bot.owner_id:
            await ctx.send(f"❌ Only the bot owner can use this command! (Your ID: {ctx.author.id})")
            return

        await ctx.send("⚠️ Are you sure you want to reset ALL bot data? Type `yes` to confirm.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=COMMAND_RESPONSE_TIMEOUT)
            if msg.content.lower() == 'yes':
                data_store.guilds = {}
                data_store.stats = {}
                data_store.save_data()
                await ctx.send("✅ All bot data has been reset!")
            else:
                await ctx.send("❌ Reset cancelled.")
        except asyncio.TimeoutError:
            await ctx.send("❌ Reset cancelled (timeout).")

    # MAINTENANCE MODE (Owner Only)

    @bot.command(name='maintenance')
    async def maintenance_mode(ctx, mode: str = None):
        """
        Toggle maintenance mode (Owner only)

        When maintenance is ON, all commands are disabled except for owner.
        This allows safe updates and fixes without user interference.

        Usage:
            +maintenance on     - Enable maintenance mode
            +maintenance off    - Disable maintenance mode
            +maintenance        - Check current status
        """
        if ctx.author.id != bot.owner_id:
            await ctx.send(f"❌ Only the bot owner can use this command! (Your ID: {ctx.author.id})")
            return

        # Check current status if no argument
        if mode is None:
            current_status = data_store.is_maintenance_mode()
            status_text = "🚧 **ENABLED**" if current_status else "✅ **DISABLED**"

            embed = discord.Embed(
                title="🔧 Maintenance Mode Status",
                description=f"Maintenance mode is currently: {status_text}",
                color=discord.Color.orange() if current_status else discord.Color.green()
            )
            embed.add_field(
                name="Commands",
                value=(
                    "`+maintenance on` - Enable maintenance\n"
                    "`+maintenance off` - Disable maintenance"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
            return

        mode = mode.lower()

        if mode == 'on':
            if data_store.is_maintenance_mode():
                await ctx.send("⚠️ Maintenance mode is already enabled!")
                return

            data_store.set_maintenance_mode(True)

            embed = discord.Embed(
                title="🚧 Maintenance Mode ENABLED",
                description=(
                    "The bot is now in maintenance mode.\n\n"
                    "Use `+maintenance off` when done."
                ),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            print("🚧 MAINTENANCE MODE ENABLED")

        elif mode == 'off':
            if not data_store.is_maintenance_mode():
                await ctx.send("⚠️ Maintenance mode is already disabled!")
                return

            data_store.set_maintenance_mode(False)

            embed = discord.Embed(
                title="✅ Maintenance Mode DISABLED",
                description=(
                    "The bot is now back online for everyone!\n\n"
                    "All commands are now accessible to all users."
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Disabled by {ctx.author.name}")
            await ctx.send(embed=embed)
            print("✅ MAINTENANCE MODE DISABLED")

        else:
            await ctx.send("❌ Invalid argument! Use `on` or `off`.\n\nExample: `+maintenance on`")
