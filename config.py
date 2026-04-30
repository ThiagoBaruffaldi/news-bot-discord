import os
import logging
import pytz
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

