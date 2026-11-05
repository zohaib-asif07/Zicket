"""
Fielding Commands Module
Handles catch statistics viewing and logging
"""

import discord
from typing import Optional

def setup_fielding_commands(bot):
    """Setup function to register fielding commands"""

    from ui.embeds import create_catch_stats_embed
    from ui.views import CatchButtonView

    # View catch stats

    @bot.command(name='catch')
    async def catch_stats(ctx, target: Optional[str] = None):
        """
        View player's fielding/catch statistics

        Usage:
            +catch              - View your own catch stats
            +catch @user        - View mentioned user's catch stats
            +catch username     - View catch stats by username
            +catch 123456789    - View catch stats by user ID
        """
        guild_id = str(ctx.guild.id)

        if target is None:
            user_id = str(ctx.author.id)
        else:
            if ctx.message.mentions:
                user_id = str(ctx.message.mentions[0].id)
            elif target.isdigit():
                user_id = target
            else:
                member = discord.utils.find(
                    lambda m: m.name.lower() == target.lower() or
                             m.display_name.lower() == target.lower(),
                    ctx.guild.members
                )
                if member:
                    user_id = str(member.id)
                else:
                    await ctx.send("❌ User not found!")
                    return

        embed = create_catch_stats_embed(user_id, guild_id, ctx.guild)
        await ctx.send(embed=embed)

    # LOG CATCH OPPORTUNITY (Admin Only)

    @bot.command(name='logcatch', aliases=['lc'])
    async def log_catch(ctx, target: Optional[str] = None):
        """
        Log a catch opportunity (Admin only)

        Creates an interactive prompt asking if the catch was taken or dropped

        Usage:
            +logcatch @user        - Log catch for mentioned user
            +logcatch username     - Log catch by username
            +logcatch 123456789    - Log catch by user ID
        """
        guild_id = str(ctx.guild.id)

        if ctx.author.id != bot.owner_id and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You need administrator permissions to use this command!")
            return

        if target is None:
            await ctx.send("❌ Please specify a user!\nUsage: `+logcatch @user` or `+logcatch username`")
            return

        if ctx.message.mentions:
            user_id = str(ctx.message.mentions[0].id)
            member = ctx.message.mentions[0]
        elif target.isdigit():
            user_id = target
            member = ctx.guild.get_member(int(user_id))
        else:
            member = discord.utils.find(
                lambda m: m.name.lower() == target.lower() or
                         m.display_name.lower() == target.lower(),
                ctx.guild.members
            )
            if member:
                user_id = str(member.id)
            else:
                await ctx.send("❌ User not found!")
                return

        username = member.name if member else f"User {user_id}"

        embed = discord.Embed(
            title="🏏 CATCH OPPORTUNITY!",
            description=f"A catch came toward **{username}**!\nDid they take the catch?",
            color=discord.Color.blue()
        )

        if member:
            embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(text="Click a button below to log the result")

        view = CatchButtonView(guild_id, user_id, username, bot.owner_id)
        await ctx.send(embed=embed, view=view)

    # Error handler
    @log_catch.error
    async def permission_error(ctx, error):
        """Handle permission errors gracefully"""
        # Don't show error for bot owner
        if ctx.author.id == bot.owner_id:
            return
        if isinstance(error, discord.ext.commands.MissingPermissions):
            await ctx.send("❌ You need administrator permissions to use this command!")
