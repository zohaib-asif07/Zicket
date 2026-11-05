"""
Admin Commands Module
Handles server configuration (prefix, logs, tournament)
"""

import discord
from discord.ext import commands
import asyncio

from config import COMMAND_RESPONSE_TIMEOUT

def setup_admin_commands(bot):
    """Setup function to register admin commands"""

    from core.data_store import data_store

    @bot.command(name='setprefix')
    async def set_prefix(ctx, prefix: str):
        """
        Change the bot prefix for this server (Admin only)

        Usage:
            +setprefix !        - Change prefix to !
            +setprefix $        - Change prefix to $
        """
        # Bot owner bypasses permission check
        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        guild_id = str(ctx.guild.id)
        data_store.init_guild(guild_id)
        data_store.guilds[guild_id]['prefix'] = prefix
        data_store.save_data()

        await ctx.send(f"✅ Prefix changed to `{prefix}`")

    @bot.command(name='setlogschannel')
    async def set_logs_channel(ctx, channel: discord.TextChannel):
        """
        Set the channel for bot logs (Admin only)

        Logs will show when stats are added/removed

        Usage:
            +setlogschannel #logs
            +setlogschannel #admin-logs
        """
        # Bot owner bypasses permission check
        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        guild_id = str(ctx.guild.id)
        data_store.init_guild(guild_id)
        data_store.guilds[guild_id]['logs_channel'] = str(channel.id)
        data_store.save_data()

        await ctx.send(f"✅ Logs channel set to {channel.mention}")

    @bot.command(name='tournament')
    async def set_tournament(ctx):
        """
        Set the current tournament name and category (Admin only)

        Usage:
            +tournament
            (Then follow the prompts)
        """
        guild_id = str(ctx.guild.id)

        # Bot owner bypasses permission check
        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        data_store.init_guild(guild_id)
        current_tournament = data_store.guilds[guild_id].get('tournament', '6PSL S1')
        current_category = data_store.guilds[guild_id].get('tournament_category', 'OTHER')

        embed = discord.Embed(
            title="🏆 Set Tournament",
            description=(
                f"**Current Tournament:** `{current_tournament}`\n"
                f"**Current Category:** `{current_category}`\n\n"
                "Please enter the new tournament name.\n\n"
                "**Examples:**\n"
                "• `BPSL 7` - BPSL Season 7\n"
                "• `BOTS 19` - BOTS Tournament 19\n"
                "• `Champions League 2026`\n"
                "• `Spring Championship`"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"You have {COMMAND_RESPONSE_TIMEOUT} seconds to respond")

        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=COMMAND_RESPONSE_TIMEOUT)
            tournament_name = msg.content.strip()

            if not tournament_name or len(tournament_name) > 50:
                error_embed = discord.Embed(
                    title="❌ Invalid Input",
                    description="Please enter a valid tournament name (1-50 characters).\n\nExample: `BPSL 7`, `BOTS 19`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return

            category_embed = discord.Embed(
                title="📂 Set Tournament Category",
                description=(
                    f"**Tournament Name:** `{tournament_name}`\n\n"
                    "Please enter the category for this tournament.\n\n"
                    "**Common Categories:**\n"
                    "• `BPSL` - BPSL tournaments\n"
                    "• `BOTS` - BOTS tournaments\n"
                    "• Or any custom category name"
                ),
                color=discord.Color.gold()
            )
            category_embed.set_footer(text=f"You have {COMMAND_RESPONSE_TIMEOUT} seconds to respond")

            await ctx.send(embed=category_embed)

            cat_msg = await bot.wait_for('message', check=check, timeout=COMMAND_RESPONSE_TIMEOUT)
            category = cat_msg.content.strip()

            if not category or len(category) > 30:
                error_embed = discord.Embed(
                    title="❌ Invalid Input",
                    description="Please enter a valid category name (1-30 characters).\n\nExample: `BPSL`, `BOTS`, `Champions League`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return

            data_store.guilds[guild_id]['tournament'] = tournament_name
            data_store.guilds[guild_id]['tournament_category'] = category.upper()
            data_store.save_data()

            success_embed = discord.Embed(
                title="✅ Tournament Updated",
                description=(
                    f"**Tournament Name:** {tournament_name}\n"
                    f"**Category:** {category.upper()}\n\n"
                    f"All current stats will count toward **{category.upper()}** all-time records."
                ),
                color=discord.Color.green()
            )
            success_embed.set_footer(text=f"Updated by {ctx.author.name}")
            await ctx.send(embed=success_embed)

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Timeout",
                description="Tournament update cancelled due to timeout.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=timeout_embed)

    @bot.command(name='setcategory')
    async def set_category(ctx, *, category: str = None):
        """
        Set category for current tournament (Admin only)

        Usage:
            +setcategory BPSL
            +setcategory Champions League
        """
        guild_id = str(ctx.guild.id)

        # Bot owner bypasses permission check
        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        if not category:
            await ctx.send("❌ Please specify a category!\n\nUsage: `+setcategory <category>`\n\nExample: `+setcategory BPSL`")
            return

        if len(category) > 30:
            await ctx.send("❌ Category name too long! Maximum 30 characters.")
            return

        data_store.init_guild(guild_id)
        current_tournament = data_store.guilds[guild_id].get('tournament', '6PSL S1')
        old_category = data_store.guilds[guild_id].get('tournament_category', 'OTHER')

        new_category = category.upper()
        data_store.set_current_tournament_category(guild_id, new_category)

        embed = discord.Embed(
            title="✅ Category Changed",
            description=(
                f"**Tournament:** {current_tournament}\n"
                f"**Old Category:** {old_category}\n"
                f"**New Category:** {new_category}\n\n"
                f"Current stats will now appear in **{new_category}** all-time records."
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Changed by {ctx.author.name}")

        await ctx.send(embed=embed)

    @bot.command(name='help')
    async def help_command(ctx):
        """Show all available commands"""

        # Basic embed for all users
        basic_embed = discord.Embed(
            title="🏏 Zicket - Commands",
            description="A comprehensive cricket statistics tracking bot",
            color=discord.Color.blue()
        )

        basic_embed.add_field(
            name="📊 Stats Commands",
            value=(
                "`+stats [@user]` - View player stats\n"
                "`+stats [@user] BOTS19` - View archived tournament stats\n"
                "`+allstats/+ast` - All Time Stats\n"
                "`+catch [@user]` - View fielding stats\n"
                "`+ping` - Check bot latency"
            ),
            inline=False
        )

        basic_embed.add_field(
            name="🏆 Leaderboard",
            value=(
                "`+lb` - Interactive server leaderboard\n"
                "`+lb BOTS19` - Archived tournament leaderboard\n"
                "`+alllb` - All time leaderboard\n"
                "`+categories` - Check all time stats categories\n"
                "`+tournamentlist` / `+tl` - List all archived tournaments"
            ),
            inline=False
        )

        basic_embed.add_field(
            name="📋 Points Table",
            value="`+pointstable` / `+pt` - View league standings",
            inline=False
        )

        basic_embed.add_field(
            name="🤖 Auto-Catch System",
            value=(
                "`+autocatchstatus` - Check auto-catch status\n"
                "`+channelstatus` - List enabled channels"
            ),
            inline=False
        )

        basic_embed.add_field(
            name="🎨 Fun",
            value=(
                "`+testwicket` / `+tw` - Test wicket graphic"
            ),
            inline=False
        )


        basic_embed.set_footer(text="ZICKET • Made with ❤️ by Zack", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        # Admin embed
        admin_embed = discord.Embed(
            title="👑 Admin & Owner Commands",
            description="Restricted commands for administrators and bot owner",
            color=discord.Color.red()
        )

        admin_embed.add_field(
            name="📋 Admin Tools",
            value=(
                "`+addstats` / `+as` - Add match stats (Admin)\n"
                "`+removestats` / `+rs` - Remove match stats (Admin)"
            ),
            inline=False
        )

        admin_embed.add_field(
            name="🏆 League Management (Admin)",
            value=(
                "`+setup` - Set up league teams\n"
                "`+matchresult` / `+mr` - Record match result\n"
                "`+resetteams` - Reset all teams"
            ),
            inline=False
        )

        admin_embed.add_field(
            name="🤖 Auto-Catch Controls (Admin)",
            value=(
                "`+logcatch @user` - Log catch manually\n"
                "`+enable` / `+disable` - Server-wide toggle\n"
                "`+enablechannel` / `+disablechannel` - Channel toggle"
            ),
            inline=False
        )

        admin_embed.add_field(
            name="⚙️ Server Settings (Admin)",
            value=(
                "`+setprefix <prefix>` - Change bot prefix\n"
                "`+setlogschannel #channel` - Set logs channel\n"
                "`+tournament` - Set tournament name"
            ),
            inline=False
        )

        admin_embed.add_field(
            name="👑 Owner Commands",
            value=(
                "`+categorize BPSL1 BPSL`\n"
                "`+grantaccess <guild_id>` - Grant server access\n"
                "`+revokeaccess <guild_id>` - Revoke server access\n"
                "`+reset <guild_id>` - Reset & archive guild data\n"
                "`+resetbot` - Reset all bot data\n"
                "`+maintenance on/off` - Toggle maintenance mode\n"
                "`+testpointstable` / `+tpt` - Test points table"
            ),
            inline=False
        )

        admin_embed.set_footer(text="Admin Only Area", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        # Check if user is admin or owner
        is_admin = ctx.author.guild_permissions.administrator or ctx.author.id == bot.owner_id

        if is_admin:
            from ui.views import AdminHelpView
            view = AdminHelpView(basic_embed, admin_embed, ctx.author)
            message = await ctx.send(embed=basic_embed, view=view)
            view.message = message
        else:
            # Send basic embed only
            await ctx.send(embed=basic_embed)

    # Error handlers
    @set_logs_channel.error
    @set_prefix.error
    async def permission_error(ctx, error):
        """Handle permission errors gracefully"""
        # Don't show error for bot owner
        if ctx.author.id == bot.owner_id:
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command!")
