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

import asyncio
import logging
import os
from datetime import datetime

import discord
import feedparser
import google.generativeai as genai
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# INITIAL SETUP
# ──────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

DISCORD_TOKEN      = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
BRASILIA_TZ        = pytz.timezone("America/Sao_Paulo")

# ──────────────────────────────────────────────
# RSS FEEDS — add or remove as needed
# ──────────────────────────────────────────────
RSS_FEEDS_GENERAL = [
    # Brazil
    "https://g1.globo.com/rss/g1/",
    "https://feeds.folha.uol.com.br/folha/mundo/rss091.xml",
    "https://feeds.folha.uol.com.br/folha/brasil/rss091.xml",
    "https://feeds.folha.uol.com.br/folha/mercado/rss091.xml",
    "https://www.uol.com.br/rss.xml",
    "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",
    # International (Portuguese/English)
    "https://www.bbc.com/portuguese/index.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.theguardian.com/world/rss",
    "https://feeds.skynews.com/feeds/rss/world.xml",
]

RSS_FEEDS_TECH = [
    "https://feeds.folha.uol.com.br/folha/tec/rss091.xml",
    "https://g1.globo.com/rss/g1/tecnologia/",
    "https://tecmundo.com.br/feed",
    "https://www.tudocelular.com/feed/noticias.xml",
    "https://olhardigital.com.br/feed/",
    "https://techcrunch.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.wired.com/wired/index",
    "https://www.cnet.com/rss/news/",
]

MAX_ITEMS_PER_FEED = 10      # items collected per feed
MAX_CHARS_GEMINI   = 90_000  # safe context limit for Gemini


# ──────────────────────────────────────────────
# RSS NEWS COLLECTION
# ──────────────────────────────────────────────
def collect_news(feeds: list[str]) -> list[dict]:
    """Iterates through RSS feeds and returns a list of news articles."""
    articles = []
    for url in feeds:
        try:
            feed   = feedparser.parse(url)
            source = feed.feed.get("title", url)
            for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
                title   = entry.get("title", "").strip()
                link    = entry.get("link", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                if title and link:
                    articles.append({
                        "title":   title,
                        "link":    link,
                        "summary": summary[:300],
                        "source":  source,
                    })
            log.info(f"Feed OK: {source} — {len(feed.entries[:MAX_ITEMS_PER_FEED])} items")
        except Exception as e:
            log.warning(f"Error reading feed {url}: {e}")
    return articles


# ──────────────────────────────────────────────
# GEMINI ANALYSIS AND SUMMARIZATION
# ──────────────────────────────────────────────
def build_news_block(articles: list[dict]) -> str:
    """Serializes the articles into plain text for the Gemini prompt."""
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(
            f"{i}. [{a['source']}] {a['title']}\n"
            f"   Link: {a['link']}\n"
            f"   Summary: {a['summary']}"
        )
    return "\n\n".join(lines)


def call_gemini(prompt: str) -> str:
    """Sends the prompt to Gemini and returns the response as plain text."""
    genai.configure(api_key=GEMINI_API_KEY)
    model    = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_general_summary(articles: list[dict]) -> str:
    """Builds the general news prompt and calls Gemini."""
    block = build_news_block(articles)[:MAX_CHARS_GEMINI]
    today = datetime.now(BRASILIA_TZ).strftime("%d/%m/%Y")

    prompt = f"""You are a professional news curator. Analyze the articles below, collected from multiple news outlets on {today}.
Write your entire response in Brazilian Portuguese.

Your task:
1. Identify WHICH TOPICS appear in MORE THAN ONE outlet (this indicates higher relevance).
2. Select the **5 most important general news stories** (exclude any story about Technology, Gadgets, Software, AI, Hardware, Startups, or similar topics).
3. Prioritize stories that appear across multiple outlets.
4. Generate the output in TWO sections, SUMARIO and RESUMOS COMPLETOS, in this order:

SUMARIO
List the 5 chosen stories, each in ONE SHORT AND DIRECT SENTENCE (15 words max), with a thematic emoji on the left representing the topic. Do not always use the same emoji — choose one that fits the theme (e.g. 🗳️ for elections, 🌊 for natural disasters, ⚽ for sports, 💊 for health, etc.).

Summary output format (do not put anything before this):
**📋 SUMÁRIO**

[emoji] [short sentence about story 1]
[emoji] [short sentence about story 2]
[emoji] [short sentence about story 3]
[emoji] [short sentence about story 4]
[emoji] [short sentence about story 5]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**✍️ RESUMOS COMPLETOS**

For each of the same 5 stories, in the same order as the summary, write:
   - **Title in Portuguese** (adapt if necessary)
   - A clear, direct, and informative summary paragraph (3-5 sentences)
   - Original article links inside angle brackets (e.g. <https://example.com>) (up to 3 links per story)

Format for each story:
🔹 **[STORY TITLE]**
[3-5 sentence summary]
🔗 <Link 1> | <Link 2> (if available)

---

Collected articles:
{block}

Remember: ONLY general news (politics, economy, health, sports, environment, international, etc.). Nothing technology-related.
Do NOT include any introductory, explanatory, or analytical text outside the two sections above. Go straight to the summary.
"""
    return call_gemini(prompt)


def generate_tech_summary(articles: list[dict]) -> str:
    """Builds the tech news prompt and calls Gemini."""
    block = build_news_block(articles)[:MAX_CHARS_GEMINI]
    today = datetime.now(BRASILIA_TZ).strftime("%d/%m/%Y")

    prompt = f"""You are a professional Technology news curator. Analyze the articles below, collected from multiple specialized tech outlets on {today}.
Write your entire response in Brazilian Portuguese.

Your task:
1. Identify which TECHNOLOGY topics appear in more than one outlet (this indicates higher relevance).
2. Select the **3 most important Technology news stories**.
3. Prioritize stories that appear across multiple outlets.
4. Generate the output in TWO sections: summary and full digests, in this order:

SUMARIO
List the 3 chosen stories, each in ONE SHORT AND DIRECT SENTENCE (15 words max), with a thematic emoji on the left representing the topic (e.g. 🤖 for AI, 📱 for smartphones, 🔐 for security, 🎮 for gaming, 🚀 for space/tech, etc.). Do not repeat emojis.

Summary output format (do not put anything before this):
**📋 SUMÁRIO**

[emoji] [short sentence about story 1]
[emoji] [short sentence about story 2]
[emoji] [short sentence about story 3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**✍️ RESUMOS COMPLETOS**

For each of the same 3 stories, in the same order as the summary, write:
   - **Title in Portuguese**
   - Clear and objective summary (3-5 sentences), including practical impact when relevant
   - Original article links inside angle brackets (e.g. <https://example.com>) (up to 3 links per story)

Format for each story:
💻 **[TECH STORY TITLE]**
[3-5 sentence summary]
🔗 <Link 1> | <Link 2> (if available)

---

Collected tech articles:
{block}

Do NOT include any introductory, explanatory, or analytical text outside the two sections above. Go straight to the summary.
"""
    return call_gemini(prompt)


# ──────────────────────────────────────────────
# FINAL DISCORD MESSAGE ASSEMBLY
# ──────────────────────────────────────────────
def build_message(general_summary: str, tech_summary: str, time: str = "06:00") -> list[str]:
    """
    Discord has a 2000-character limit per message.
    This function returns a list of parts for sequential sending.
    """
    date_str = datetime.now(BRASILIA_TZ).strftime("%d/%m/%Y")

    header = (
        f"# 📰 News Digest — {date_str}\n"
        f"*Automatically generated at {time} (Brasília time)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    separator = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    general_body = (
        "# 🌎 Top 5 — Notícias Gerais\n\n"
        + general_summary
    )

    tech_body = (
        "\n# 🖥️ Top 3 — Tecnologia\n\n"
        + tech_summary
    )

    full_text = header + general_body + separator + tech_body

    # Split into chunks of up to 1990 chars, respecting line breaks
    parts = []
    while len(full_text) > 1990:
        cut = full_text[:1990].rfind("\n")
        if cut == -1:
            cut = 1990
        parts.append(full_text[:cut])
        full_text = full_text[cut:].lstrip("\n")
    parts.append(full_text)

    return parts


# ──────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────
async def run_pipeline(channel: discord.TextChannel, time: str = "06:00"):
    """Collects news, analyzes with Gemini, and posts the digest to the channel."""
    await channel.send("⏳ *Collecting and analyzing today's news... please wait a moment.*")

    loop = asyncio.get_event_loop()

    # Collect in a separate thread to avoid blocking the bot
    log.info("Collecting general feeds...")
    general_articles = await loop.run_in_executor(None, collect_news, RSS_FEEDS_GENERAL)

    log.info("Collecting tech feeds...")
    tech_articles = await loop.run_in_executor(None, collect_news, RSS_FEEDS_TECH)

    log.info(f"Total collected: {len(general_articles)} general | {len(tech_articles)} tech")

    # Generate summaries with Gemini
    log.info("Generating general summary with Gemini...")
    general_summary = await loop.run_in_executor(None, generate_general_summary, general_articles)

    log.info("Generating tech summary with Gemini...")
    tech_summary = await loop.run_in_executor(None, generate_tech_summary, tech_articles)

    # Assemble and send
    parts = build_message(general_summary, tech_summary, time)
    for part in parts:
        await channel.send(part)
        await asyncio.sleep(0.5)  # avoid rate limiting

    log.info("Digest posted successfully!")


# ──────────────────────────────────────────────
# DISCORD BOT
# ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot       = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler(timezone=BRASILIA_TZ)


@bot.event
async def on_ready():
    log.info(f"Bot connected as {bot.user} (ID: {bot.user.id})")

    # Schedule the daily digest at 06:00 Brasília time
    scheduler.add_job(
        daily_task,
        CronTrigger(hour=6, minute=0, timezone=BRASILIA_TZ),
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler active: daily digest at 06:00 (Brasília)")


async def daily_task():
    """Called automatically by the scheduler at 06:00."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        log.error(f"Channel {DISCORD_CHANNEL_ID} not found. Check DISCORD_CHANNEL_ID in .env")
        return
    try:
        await run_pipeline(channel, time="06:00")
    except Exception as e:
        log.exception(f"Error in daily task: {e}")
        await channel.send(f"❌ An error occurred while generating the daily digest: `{e}`")


@bot.command(name="summary")
async def summary(ctx: commands.Context):
    """
    !summary command — generates and posts the digest immediately.
    Does not interfere with the 06:00 scheduled task.
    """
    current_time = datetime.now(BRASILIA_TZ).strftime("%H:%M")
    log.info(f"!summary triggered by {ctx.author} at {current_time}")
    try:
        await run_pipeline(ctx.channel, time=current_time)
    except Exception as e:
        log.exception(f"Error in !summary: {e}")
        await ctx.send(f"❌ An error occurred while generating the digest: `{e}`")


@bot.command(name="status")
async def status(ctx: commands.Context):
    """Displays information about the next scheduled digest."""
    job = scheduler.get_job("daily_digest")
    if job:
        next_run = job.next_run_time.astimezone(BRASILIA_TZ).strftime("%d/%m/%Y at %H:%M")
        await ctx.send(f"✅ Bot is active! Next automatic digest: **{next_run}** (Brasília time)")
    else:
        await ctx.send("⚠️ No active schedule found.")


@bot.command(name="help")
async def help_command(ctx: commands.Context):
    """Lists all available commands."""
    msg = (
        "**📋 Available commands:**\n"
        "`!summary` — Generates and posts the news digest right now\n"
        "`!status`  — Shows when the next automatic digest will be sent\n"
        "`!help`    — Displays this message\n\n"
        "📅 The automatic digest is sent **every day at 06:00** (Brasília time)."
    )
    await ctx.send(msg)


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
