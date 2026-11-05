"""
Auto-Catch Toggle Commands Module
Handles enabling/disabling automatic catch logging (Admin only)
"""

import discord
from discord.ext import commands
from discord.ui import View

def setup_auto_catch_toggle(bot):
    """Setup function to register auto-catch toggle commands"""

    from core.data_store import data_store

    # ENABLE AUTO-CATCH (Server-Wide)

    @bot.command(name='enable')
    async def enable_auto_catch(ctx):
        """
        Enable automatic catch logging for entire server (Admin only)

        Usage:
            +enable
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        # Check if already enabled
        if data_store.is_auto_catch_enabled(guild_id):
            embed = discord.Embed(
                title="⚠️ Already Enabled",
                description="Automatic catch logging is already enabled for this server!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        data_store.set_auto_catch_server(guild_id, True)

        embed = discord.Embed(
            title="✅ Auto-Catch Enabled (Server)!",
            description=(
                "Automatic catch logging is now **ON** for this server.\n\n"
                "**Note:** Use `+enablechannel` in each channel where you want auto-catch.\n\n"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Enabled by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    # DISABLE AUTO-CATCH (Server-Wide)

    @bot.command(name='disable')
    async def disable_auto_catch(ctx):
        """
        Disable automatic catch logging for entire server (Admin only)

        Usage:
            +disable
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        # Check if already disabled
        if not data_store.is_auto_catch_enabled(guild_id):
            embed = discord.Embed(
                title="⚠️ Already Disabled",
                description="Automatic catch logging is already disabled for this server!",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        data_store.set_auto_catch_server(guild_id, False)

        embed = discord.Embed(
            title="🔴 Auto-Catch Disabled (Server)",
            description=(
                "Automatic catch logging is now **OFF** for this server.\n\n"
                "**Manual logging still works:**\n\n"
                "• Use `+logcatch @user` to log catches manually\n"
                "• All existing stats are preserved\n\n"
                "Use `+enable` to turn on automatic logging again."
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Disabled by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    # ENABLE AUTO-CATCH (Channel-Specific)

    @bot.command(name='enablechannel')
    async def enable_channel(ctx):
        """
        Enable automatic catch logging for current channel (Admin only)

        Usage:
            +enablechannel
        """
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        # Check if server is enabled
        if not data_store.is_auto_catch_enabled(guild_id):
            embed = discord.Embed(
                title="⚠️ Server Not Enabled",
                description=(
                    "The server must be enabled first!\n\n"
                    "Use `+enable` to enable the server, then use `+enablechannel` in specific channels."
                ),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return

        data_store.set_auto_catch_channel(guild_id, channel_id, True)

        embed = discord.Embed(
            title="✅ Channel Enabled!",
            description=(
                f"Automatic catch logging is now **ON** for {ctx.channel.mention}.\n\n"
                "**Auto-catch is now active in this channel!** 🎉\n\n"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Enabled by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    # DISABLE AUTO-CATCH (Channel-Specific)

    @bot.command(name='disablechannel')
    async def disable_channel(ctx):
        """
        Disable automatic catch logging for current channel (Admin only)

        Usage:
            +disablechannel
        """
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        if ctx.author.id != bot.owner_id:
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("❌ You need administrator permissions to use this command!")
                return

        data_store.set_auto_catch_channel(guild_id, channel_id, False)

        embed = discord.Embed(
            title="🔴 Channel Disabled",
            description=(
                f"Automatic catch logging is now **OFF** for {ctx.channel.mention}.\n\n"
                "**Manual logging still works:**\n"
                "• Use `+logcatch @user` to log catches manually\n\n"
                "Use `+enablechannel` to turn it back on."
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Disabled by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    # Check auto-catch status

    @bot.command(name='autocatchstatus')
    async def auto_catch_status(ctx):
        """
        Check if automatic catch logging is enabled

        Usage:
            +autocatchstatus
        """
        guild_id = str(ctx.guild.id)
        channel_id = str(ctx.channel.id)

        server_enabled = data_store.is_auto_catch_enabled(guild_id)
        channel_enabled = data_store.is_auto_catch_enabled(guild_id, channel_id)

        if server_enabled and channel_enabled:
            embed = discord.Embed(
                title="✅ Auto-Catch Status",
                description="Automatic catch logging is **ACTIVE** in this channel!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Server Status",
                value="✅ Enabled",
                inline=True
            )
            embed.add_field(
                name="Channel Status",
                value="✅ Enabled",
                inline=True
            )
            embed.add_field(
                name="Result",
                value="🎉 **Auto-catch is working!**",
                inline=False
            )
        elif server_enabled and not channel_enabled:
            embed = discord.Embed(
                title="⚠️ Auto-Catch Status",
                description="Server is enabled, but this channel is disabled.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Server Status",
                value="✅ Enabled",
                inline=True
            )
            embed.add_field(
                name="Channel Status",
                value="❌ Disabled",
                inline=True
            )
            embed.add_field(
                name="To Enable",
                value="Use `+enablechannel` in this channel",
                inline=False
            )
        elif not server_enabled:
            embed = discord.Embed(
                title="🔴 Auto-Catch Status",
                description="Automatic catch logging is **DISABLED** for this server.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Server Status",
                value="❌ Disabled",
                inline=True
            )
            embed.add_field(
                name="Channel Status",
                value="N/A",
                inline=True
            )
            embed.add_field(
                name="To Enable",
                value="Use `+enable` first, then `+enablechannel` in each channel",
                inline=False
            )

        await ctx.send(embed=embed)

    # List enabled channels

    @bot.command(name='channelstatus')
    async def channel_status(ctx):
        """
        Show all enabled channels in this server (with pagination)

        Usage:
            +channelstatus
        """
        from ui.embeds import create_channel_status_embed
        from ui.views import ChannelStatusPrevButton, ChannelStatusNextButton

        guild_id = str(ctx.guild.id)
        page = 0  # Start on first page

        embed = create_channel_status_embed(guild_id, page, ctx.guild)

        # Check if we need pagination
        data_store.init_guild(guild_id)
        auto_catch_channels = data_store.guilds[guild_id].get('auto_catch_channels', {})
        enabled_channels = [ch_id for ch_id, enabled in auto_catch_channels.items() if enabled]
        total_pages = (len(enabled_channels) - 1) // 10 + 1 if enabled_channels else 1

        # Create view with buttons only if multiple pages
        if total_pages > 1:
            view = View()
            view.add_item(ChannelStatusPrevButton(guild_id, page))
            view.add_item(ChannelStatusNextButton(guild_id, page))
            await ctx.send(embed=embed, view=view)
        else:
            # No buttons needed for single page
            await ctx.send(embed=embed)

    # Error handlers
    @enable_auto_catch.error
    @disable_auto_catch.error
    @enable_channel.error
    @disable_channel.error
    async def toggle_error(ctx, error):
        """Handle permission errors gracefully"""
        if ctx.author.id == bot.owner_id:
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command!")
