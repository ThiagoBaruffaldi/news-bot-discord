"""
╔══════════════════════════════════════════════════════════════╗
║           DISCORD BOT - DAILY NEWS DIGEST                    ║
║                  Powered by Gemini API                       ║
╚══════════════════════════════════════════════════════════════╝

REQUIRED LIBRARIES — run in the VSCode terminal:
    pip install discord.py feedparser google-generativeai apscheduler pytz aiohttp

ENVIRONMENT VARIABLES — create a .env file in the same folder:
    DISCORD_TOKEN=your_bot_token_here
    GEMINI_API_KEY=your_gemini_api_key_here
    DISCORD_CHANNEL_ID=channel_id_to_post_in   (number, no quotes)

    pip install python-dotenv   ← also required to load the .env file
"""

from config import DISCORD_TOKEN, GEMINI_API_KEY, DISCORD_CHANNEL_ID
from bot import bot

# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN is not defined in the .env file")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not defined in the .env file")
    if DISCORD_CHANNEL_ID == 0:
        raise ValueError("DISCORD_CHANNEL_ID is not defined in the .env file")

    bot.run(DISCORD_TOKEN)
