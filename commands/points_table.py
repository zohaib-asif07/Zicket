"""
Points Table Commands Module
Generates visual points table graphics for the league
"""

import discord
from utils.points_table_graphics import generate_points_table_graphic

def setup_points_table_commands(bot):
    """Setup function to register points table commands"""

    @bot.command(name='testpointstable', aliases=['tpt'])
    async def test_points_table(ctx):
        """
        Generate a test points table graphic

        Usage:
            +testpointstable
            +tpt
        """
        if ctx.author.id != bot.owner_id:
        	await ctx.send("❌ Only the bot owner can use this command for now!")
        	return
        try:
            # Test data for teams
            teams = [
                {
                    'name': 'Forward Point',
                    'color': (5, 255, 186, 180),  # Cyan-Green (RGBA)
                    'logo': 'allstars.png',
                    'played': 8,
                    'won': 4,
                    'lost': 4,
                    'points': 8
                },
                {
                    'name': 'Tandoori Talibans',
                    'color': (217, 142, 3, 180),  # Orange-Gold (RGBA)
                    'logo': 'talibans.png',
                    'played': 8,
                    'won': 5,
                    'lost': 3,
                    'points': 10
                },
                {
                    'name': 'Hyderabad Hawks',
                    'color': (0, 103, 182, 180),  # Blue (RGBA)
                    'logo': 'hawks.png',
                    'played': 7,
                    'won': 6,
                    'lost': 1,
                    'points': 12
                },
                {
                    'name': 'Colonisers',
                    'color': (175, 56, 255, 180),  # Purple-Pink (RGBA)
                    'logo': 'colonisers.png',
                    'played': 8,
                    'won': 3,
                    'lost': 5,
                    'points': 6
                },
                {
                    'name': 'Scrubs 3.0',
                    'color': (237, 197, 122),  # Light Purple (RGBA)
                    'logo': 'scrubs_3.0.png',
                    'played': 7,
                    'won': 2,
                    'lost': 5,
                    'points': 4
                },
                {
                    'name': 'Sixth Spartan',
                    'color': (255, 99, 71, 180),  # Tomato Red (RGBA)
                    'logo': 'default_logo.png',
                    'played': 8,
                    'won': 4,
                    'lost': 4,
                    'points': 8
                }
            ]

            image_binary = await generate_points_table_graphic(teams)

            await ctx.send(
                file=discord.File(fp=image_binary, filename='points_table.png')
            )

        except Exception as e:
            await ctx.send(f"❌ Error generating points table graphic: {str(e)}")
            print(f"❌ Test points table error: {e}")
            import traceback
            traceback.print_exc()
