import asyncio
import logging
import discord
from datetime import datetime
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import DISCORD_CHANNEL_ID, BRASILIA_TZ, RSS_FEEDS_GENERAL, RSS_FEEDS_TECH
from collector import collect_news
from gemini import generate_general_summary, generate_tech_summary

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# FINAL DISCORD MESSAGE ASSEMBLY
# ──────────────────────────────────────────────
def build_message(general_summary: str, tech_summary: str, time: str = "6:00") -> list[str]:
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
        "# 🌎 Top 5 — General News\n\n"
        + general_summary
    )

    tech_body = (
        "\n# 🖥️ Top 3 — Technology\n\n"
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
async def run_pipeline(channel: discord.TextChannel, time: str = "6:00"):
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

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
scheduler = AsyncIOScheduler(timezone=BRASILIA_TZ) #Adaptd to the target audience


@bot.event
async def on_ready():
    log.info(f"Bot connected as {bot.user} (ID: {bot.user.id})")

    # Schedule the daily digest at 6:00 Brasília time
    scheduler.add_job(
        daily_task,
        CronTrigger(hour=6, minute=0, timezone=BRASILIA_TZ), #Adaptd to the target audience
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler active: daily digest at 6:00 (Brasília)") 

async def daily_task():
    """Called automatically by the scheduler at 6:00."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        log.error(f"Channel {DISCORD_CHANNEL_ID} not found. Check DISCORD_CHANNEL_ID in .env")
        return

    MAX_ATTEMPTS = 3
    SLEEP_SECONDS = 300  # 5 minutes

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            log.info(f"Attempt {attempt} of {MAX_ATTEMPTS}...")
            await run_pipeline(channel, time="6:00")
            return  # success, exit the loop
        except Exception as e:
            log.exception(f"Attempt failed {attempt}: {e}")
            if attempt < MAX_ATTEMPTS:
                log.info(f"Waiting {SLEEP_SECONDS // 60} minutes before trying again...")
                await asyncio.sleep(SLEEP_SECONDS)
            else:
                log.error("All attempts failed.")
                await channel.send(f"❌ The daily digest failed after {MAX_ATTEMPTS} attempts. Last error: `{e}`")


@bot.command(name="summary")
async def summary(ctx: commands.Context):
    """
    !summary command — generates and posts the digest immediately.
    Does not interfere with the 6:00 scheduled task.
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
        "📅 The automatic digest is sent **every day at 6:00** (Brasília time)."
    )
    await ctx.send(msg)

