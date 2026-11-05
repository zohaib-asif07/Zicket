# Zicket

Zicket is a Discord bot that tracks Hand Cricket stats for leagues and tournaments. It reads the HandCricket bot's match messages and builds player stats, leaderboards, points tables and match graphics.

## Features

- **Player stats:** batting, bowling and fielding stats with ratings, roles and fantasy points
- **Leaderboards:** interactive leaderboards for the current tournament, archived tournaments and all-time records
- **Tournament archive:** archive a finished tournament, group tournaments into categories and view all-time stats per category
- **Auto-catch:** detects catch chances from the HandCricket bot and logs them, per server or per channel
- **Wicket graphics:** posts an image card when a batter gets out
- **Power Surge:** captains and vice-captains can activate a Power Surge over
- **Points table:** team setup with logos, match results and a generated points table image
- **Server settings:** custom prefix, logs channel and maintenance mode

## Setup

1. Install Python 3.10 or newer.
2. Clone the repo and install the requirements:
   ```bash
   git clone https://github.com/zohaib-asif07/Zicket.git
   cd Zicket
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project folder with your values:
   ```
   DISCORD_BOT_TOKEN=your-bot-token
   OWNER_ID=your-discord-user-id
   CAPTAIN_ROLE_ID=...
   VICE_CAPTAIN_ROLE_ID=...
   ```
4. In the [Discord Developer Portal](https://discord.com/developers/applications), turn on the **Message Content** and **Server Members** intents for your bot.
5. Start the bot:
   ```bash
   python main.py
   ```
6. In your server, run `+grantaccess <server_id>` as the owner to enable stats commands there.

## Commands

The default prefix is `+`. Run `+help` in Discord for the full list.

| Command | What it does |
| - | - |
| `+stats [@user] [tournament]` | Player stats |
| `+catch [@user]` | Fielding stats |
| `+lb [tournament]` | Leaderboard |
| `+allstats` / `+alllb` | All-time stats and leaderboard |
| `+pointstable` / `+pt` | League points table |
| `+powersurge` / `+ps` | Activate Power Surge (captains) |
| `+addstats` / `+removestats` | Add or remove match stats (admin) |
| `+setup` / `+matchresult` | Set up teams and record results (admin) |
| `+enable` / `+disable` | Toggle auto-catch (admin) |
| `+setprefix` / `+setlogschannel` / `+tournament` | Server settings (admin) |
| `+grantaccess` / `+reset` / `+maintenance` | Owner tools |

## Project structure

```
main.py            entry point
config.py          settings and IDs (read from .env)
core/              bot class, events and data storage
commands/          command modules
ui/                embeds and interactive views
utils/             calculations, parsers and image generation
```

The `assets/` folder (backgrounds, fonts and the default team logo) is not included in this repo. Without it, the wicket graphic and points table images won't work.

Bot data (stats, teams, archived tournaments) is saved as JSON files next to `main.py` while the bot runs. Those files are not committed to the repo.
