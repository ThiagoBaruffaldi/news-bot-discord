import logging
import feedparser
from config import MAX_ITEMS_PER_FEED

log = logging.getLogger(__name__)

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
