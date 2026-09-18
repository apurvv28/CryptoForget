import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

# Public RSS news endpoints categorized for real-world live news fetching
RSS_FEEDS = {
    "all": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    "technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en",
    "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en",
    "sports": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-IN&gl=IN&ceid=IN:en",
    "entertainment": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-IN&gl=IN&ceid=IN:en",
    "science": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-IN&gl=IN&ceid=IN:en",
    "health": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-IN&gl=IN&ceid=IN:en",
}

# In-memory cache for live news articles
_LIVE_NEWS_CACHE: List[Dict[str, Any]] = []


def _clean_html_text(raw_html: str) -> str:
    """Removes HTML tags and cleans snippet text."""
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw_html)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    return clean.strip()


def fetch_live_news_articles(category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    """Fetches real-time live news articles from global news RSS feeds."""
    global _LIVE_NEWS_CACHE

    cat_key = (category or "all").lower()
    feed_url = RSS_FEEDS.get(cat_key, RSS_FEEDS["all"])

    articles: List[Dict[str, Any]] = []

    try:
        req = urllib.request.Request(
            feed_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        for idx, item in enumerate(items[:limit]):
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            description = item.findtext("description", default="")
            pub_date = item.findtext("pubDate", default="")
            source = item.findtext("source", default="Live News")

            cleaned_abstract = _clean_html_text(description)
            if not cleaned_abstract:
                cleaned_abstract = title

            # Generate unique live news ID
            news_hash = hashlib.md5(f"{title}_{link}".encode("utf-8")).hexdigest()[:8].upper()
            news_id = f"LIVE-{news_hash}"

            article = {
                "news_id": news_id,
                "category": cat_key.capitalize() if cat_key != "all" else "Top News",
                "subcategory": source,
                "title": title,
                "abstract": cleaned_abstract,
                "url": link,
                "published_at": pub_date,
                "is_live": True,
            }
            articles.append(article)

        if articles:
            # Update live cache
            existing_ids = {a["news_id"] for a in _LIVE_NEWS_CACHE}
            for a in articles:
                if a["news_id"] not in existing_ids:
                    _LIVE_NEWS_CACHE.insert(0, a)

    except Exception as exc:
        print(f"[LiveNewsFetcher] Warning: Failed to fetch live RSS feed ({exc}). Using cached live news.")

    return articles or _LIVE_NEWS_CACHE[:limit]
