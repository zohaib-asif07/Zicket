"""
Points Table Graphics Module
Generates visual points table graphics using team data
"""

import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
TEAM_LOGOS_DIR = os.path.join(ASSETS_DIR, 'team_logos')

def get_asset_path(filename: str) -> str:
    """
    Get full path to asset file

    Args:
        filename: Asset filename

    Returns:
        Full path to asset
    """
    return os.path.join(ASSETS_DIR, filename)

def get_logo_path(filename: str) -> str:
    """
    Get full path to team logo file

    Args:
        filename: Logo filename

    Returns:
        Full path to logo in team_logos folder
    """
    return os.path.join(TEAM_LOGOS_DIR, filename)

async def generate_points_table_graphic(teams: List[Dict]) -> BytesIO:
    """
    Generate points table graphic image with Team Logos

    Args:
        teams: List of team dictionaries with keys:
            - name: Team name (str)
            - color: RGBA tuple (R, G, B, A)
            - logo: Logo filename (str)
            - played: Matches played (int)
            - won: Matches won (int)
            - lost: Matches lost (int)
            - points: Total points (int)

    Returns:
        BytesIO object containing the PNG image
    """

    # Sort teams by points (descending), then by wins if tied
    sorted_teams = sorted(teams, key=lambda x: (x['points'], x['won'], -x['played']), reverse=True)

    img = Image.open(get_asset_path("points_table_bg.png")).convert("RGBA")
    draw = ImageDraw.Draw(img, 'RGBA')

    try:
        team_font = ImageFont.truetype(get_asset_path("Montserrat-SemiBold.ttf"), 32)
        stats_font = ImageFont.truetype(get_asset_path("Montserrat-SemiBold.ttf"), 36)
    except Exception as e:
        print(f"⚠️ Could not load custom fonts: {e}")
        team_font = ImageFont.load_default()
        stats_font = ImageFont.load_default()

    # Positioning coordinates
    row_positions = [260, 360, 456, 554, 648, 742]
    row_height = 78

    color_box_x = 26
    color_box_width = 1002

    # Logo Settings
    logo_size = (60, 60)  # Fits inside 78px height
    logo_x_start = 40

    # Text X-coordinates (shifted for logo)
    team_name_x = 115    # Moved right to make room for logo
    played_x = 540
    won_x = 677
    lost_x = 808
    points_x = 942

    # Draw each team
    for idx, team in enumerate(sorted_teams):
        if idx >= 6:
            break

        y_pos = row_positions[idx]
        # Calculate the vertical middle of the row for perfect alignment
        row_mid_y = y_pos + (row_height // 2)

        # --- 1. Draw colored box ---
        color_box = [
            (color_box_x, y_pos),
            (color_box_x + color_box_width, y_pos + row_height)
        ]
        draw.rectangle(color_box, fill=team['color'])

        try:
            # Get logo filename from team dictionary
            logo_filename = team.get('logo', 'default_logo.png')

            # Look for logo in team_logos folder
            logo_path = get_logo_path(logo_filename)

            # If not found, try assets root folder as fallback
            if not os.path.exists(logo_path):
                logo_path = get_asset_path(logo_filename)

            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                logo = logo.resize(logo_size, Image.LANCZOS)

                # Center logo vertically
                logo_y = y_pos + (row_height - logo_size[1]) // 2
                img.paste(logo, (logo_x_start, logo_y), logo)
            else:
                print(f"⚠️ Logo not found: {logo_path}")

        except Exception as e:
            print(f"⚠️ Error loading logo for {team['name']}: {e}")
            # Continue without logo if it fails

        # --- 3. Draw team name ---
        # Use anchor="lm" for Left-Middle alignment
        draw.text(
            (team_name_x, row_mid_y),
            team['name'].upper()[:25],  # Uppercase and limit length
            font=team_font,
            fill=(0, 0, 0, 255), # color of teams
            anchor="lm"
        )

        # --- 4. Draw stats (P, W, L, Pts) ---
        # Use anchor="mm" for Middle-Middle alignment (Perfect centering)
        stat_color = (0, 0, 0, 255) # color of pts

        draw.text(
            (played_x, row_mid_y),
            str(team['played']),
            font=stats_font,
            fill=stat_color,
            anchor="mm"
        )

        draw.text(
            (won_x, row_mid_y),
            str(team['won']),
            font=stats_font,
            fill=stat_color,
            anchor="mm"
        )

        draw.text(
            (lost_x, row_mid_y),
            str(team['lost']),
            font=stats_font,
            fill=stat_color,
            anchor="mm"
        )

        draw.text(
            (points_x, row_mid_y),
            str(team['points']),
            font=stats_font,
            fill=stat_color,
            anchor="mm"
        )

    image_binary = BytesIO()
    img.save(image_binary, 'PNG')
    image_binary.seek(0)

    return image_binary
