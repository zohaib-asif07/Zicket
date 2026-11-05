"""
Wicket Graphics Module
Generates beautiful wicket graphics when batters get out
"""

import discord
import re
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
from config import CRICKET_BOT_ID

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')

def get_asset_path(filename: str) -> str:
    """
    Get full path to asset file

    Args:
        filename: Asset filename

    Returns:
        Full path to asset
    """
    return os.path.join(ASSETS_DIR, filename)

async def generate_wicket_graphic(
    batter_name: str,
    score: str,
    balls: str,
    strike_rate: float,
    dismissal_type: str,
    avatar_url: Optional[str] = None
) -> BytesIO:
    """
    Generate wicket graphic image

    Args:
        batter_name: Name of the batter who got out
        score: Runs scored
        balls: Balls faced
        strike_rate: Strike rate
        dismissal_type: Dismissal description (e.g., "C. BABAR B. SHAHEEN")
        avatar_url: URL to player's Discord avatar

    Returns:
        BytesIO object containing the PNG image
    """
    img = Image.open(get_asset_path("bg.jpg"))
    draw = ImageDraw.Draw(img)

    # PLAYER NAME (Top, Large)
    name_font = ImageFont.truetype(get_asset_path("X-Heighting.otf"), 118)
    draw.text((445, 14), batter_name[:14].upper(), font=name_font, fill="white")

    # SCORE (Right side, Very Large)
    score_font = ImageFont.truetype(get_asset_path("X-Heighting.otf"), 150)
    score_width = score_font.getlength(score) // 2
    draw.text((1550 - score_width, -7.5), score, font=score_font, fill="white")

    # BALLS (Below score)
    balls_font = ImageFont.truetype(get_asset_path("Helvetica-Bold.ttf"), 60)
    balls_width = balls_font.getlength(balls) // 2
    draw.text((1550 - balls_width, 180), balls, font=balls_font, fill="white")

    # Dismissal type
    dismissal_font = ImageFont.truetype(get_asset_path("Helvetica-Bold.ttf"), 50)
    draw.text((445, 180), dismissal_type.upper(), font=dismissal_font, fill="white")

    # Strike rate
    strike_font = ImageFont.truetype(get_asset_path("Helvetica-Bold.ttf"), 50)
    draw.text((445, 310), f"STRIKE RATE: {strike_rate}", font=strike_font, fill="white")

    # Add player avatar
    if avatar_url:
        try:
            # Download and process avatar
            avatar_data = BytesIO(await avatar_url.read())
            avatar_img = Image.open(avatar_data).convert("RGBA")
            avatar_img = avatar_img.resize((413, 416), Image.LANCZOS)
            img.paste(avatar_img, (0, 0), avatar_img)
        except Exception as e:
            print(f"⚠️  Could not load avatar: {e}")

    image_binary = BytesIO()
    img.save(image_binary, 'PNG')
    image_binary.seek(0)

    return image_binary

async def process_batter_out_message(message: discord.Message, bot) -> None:
    """
    Process "Batter out!" messages from cricket bot and generate graphics

    Args:
        message: Discord message from cricket bot
        bot: Bot instance
    """
    # Must be from cricket bot with embed
    if message.author.id != CRICKET_BOT_ID:
        return

    if not message.embeds:
        return

    embed = message.embeds[0]

    # Check if this is a "Batter out!" embed
    if not embed.title or embed.title != "Batter out!":
        return

    try:
        # Extract batter name
        batter_name = embed.fields[0].name
        batter_member = message.guild.get_member_named(batter_name)

        # Extract score and balls using regex
        match = re.search(r'(\d+)\s*\((\d+)\)', embed.fields[0].value)
        if not match:
            print("⚠️  Could not parse score/balls from embed")
            return

        score, balls = match.groups()

        strike_rate = round(int(score) / int(balls) * 100, 1) if int(balls) > 0 else 0.0

        bowler_name = embed.fields[1].name
        catcher_name = None

        # Check if it was a catch
        if embed.description and "Caught by" in embed.description:
            catcher_id_match = re.search(r'[0-9]{15,19}', embed.description)
            if catcher_id_match:
                catcher = message.guild.get_member(int(catcher_id_match.group()))
                catcher_name = catcher.name if catcher else "BOT"
            else:
                catcher_name = "BOT"

        if catcher_name:
            dismissal_type = f"C. {catcher_name[:10]} B. {bowler_name[:14]}"
        else:
            dismissal_type = f"B. {bowler_name[:14]}"

        avatar_url = None
        if batter_member and batter_member.avatar:
            avatar_url = batter_member.avatar

        image_binary = await generate_wicket_graphic(
            batter_name=batter_name,
            score=score,
            balls=balls,
            strike_rate=strike_rate,
            dismissal_type=dismissal_type,
            avatar_url=avatar_url
        )

        await message.channel.send(
            file=discord.File(fp=image_binary, filename='wicket.png')
        )

    except Exception as e:
        print(f"❌ Error generating wicket graphic: {e}")
