"""
Wicket Graphics Commands Module
Test commands for wicket graphics generation
"""

import discord
from utils.wicket_graphics import generate_wicket_graphic

def setup_wicket_commands(bot):
    """Setup function to register wicket graphics commands"""

    @bot.command(name='testwicket', aliases=['tw'])
    async def test_wicket(ctx):
        """
        Generate a test wicket graphic

        Usage:
            +testwicket
            +tw
        """
        try:
            # Use the command user's data for test
            batter_name = ctx.author.name
            score = "99"
            balls = "29"
            strike_rate = 341.4
            dismissal_type = "C. BABAR B. SHAHEEN"

            avatar_url = ctx.author.avatar if ctx.author.avatar else None

            image_binary = await generate_wicket_graphic(
                batter_name=batter_name,
                score=score,
                balls=balls,
                strike_rate=strike_rate,
                dismissal_type=dismissal_type,
                avatar_url=avatar_url
            )

            await ctx.send(
                file=discord.File(fp=image_binary, filename='test_wicket.png')
            )

        except Exception as e:
            await ctx.send(f"❌ Error generating test wicket graphic: {str(e)}")
            print(f"❌ Test wicket error: {e}")
