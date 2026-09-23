"""
Related-image resolution for live news articles.

Why this exists
---------------
Google News RSS items carry no image, and their `link` is a news.google.com
redirect rather than the publisher's page. To show a picture that belongs to
the story we:

  1. Resolve the Google News link to the real publisher article URL.
  2. Fetch only the <head> of that page and read its og:image / twitter:image
     (the image the publisher itself chose for that exact story).
  3. Verify the page really is the same story (its og:title must overlap the
     RSS headline) and that the image is not a logo/placeholder/Google asset.

If any step fails we return None and the UI keeps its generated cover tile.
We never substitute a stock or "similar" image, so an image is either the
story's own image or absent.

Resolution is slow (two network hops per article), so it runs in a small
thread pool with an in-memory cache. `enrich_articles` waits a short time
budget; anything unfinished keeps resolving in the background and is picked up
by the `/api/v1/news/images` polling endpoint.
"""

from __future__ import annotations

import base64
import re
import threading
import time
import urllib.request
import zlib
from concurrent.futures import Future, ThreadPoolExecutor, wait
from html.parser import HTMLParser
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

# ---------------------------------------------------------------- settings --
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
FETCH_TIMEOUT = 6.0            # seconds per HTTP request
MAX_HEAD_BYTES = 400_000       # never download more than this per page
MAX_WORKERS = 6                # keep modest: Google rate-limits bursts
TTL_FOUND = 6 * 3600           # keep a resolved image for 6 hours
TTL_MISSING = 15 * 60          # retry a miss after 15 minutes
CACHE_LIMIT = 2000
TITLE_OVERLAP_MIN = 0.4        # share of headline words the page title must contain

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="news-img")
_lock = threading.Lock()
# news_id -> (expires_at, image_url_or_None)
_cache: Dict[str, Tuple[float, Optional[str]]] = {}
_inflight: Dict[str, Future] = {}


# ------------------------------------------------ 1) Google News -> publisher --
_GNEWS_ID = re.compile(r"/(?:rss/)?(?:articles|read)/([^/?#]+)")
_URL_IN_BYTES = re.compile(rb"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+")


def _legacy_decode(google_url: str) -> Optional[str]:
    """Older Google News ids are plain base64 with the URL inside. Offline, instant."""
    m = _GNEWS_ID.search(google_url)
    if not m:
        return None
    token = m.group(1)
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    except Exception:
        return None
    hit = _URL_IN_BYTES.search(raw)
    if not hit:
        return None
    url = hit.group(0).decode("ascii", "ignore")
    return None if _is_google_host(url) else url


def _publisher_url(link: str) -> Optional[str]:
    """Return the real article URL for a Google News link (or the link itself if it is not one)."""
    if not link:
        return None
    if "news.google.com" not in urlparse(link).netloc:
        return link  # already a publisher URL

    url = _legacy_decode(link)
    if url:
        return url

    try:  # newer ids need Google's batchexecute lookup; delegated to a maintained library
        from googlenewsdecoder import gnewsdecoder

        res = gnewsdecoder(link, timeout=FETCH_TIMEOUT)
        ok = res.get("success", res.get("status"))
        decoded = res.get("decoded_url")
        if ok and decoded and not _is_google_host(decoded):
            return decoded
    except Exception as exc:  # library missing, blocked, or Google changed format
        print(f"[NewsImages] decode failed: {exc}")
    return None


# ------------------------------------------------------ 2) fetch <head> + parse --
class _HeadParser(HTMLParser):
    """Collects og/twitter meta tags and <title>; stops caring after </head>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: Dict[str, List[str]] = {}
        self.image_src: Optional[str] = None
        self.title = ""
        self._in_title = False
        self.done = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if self.done:
            return  # only the document <head> is trustworthy
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower().strip()
            content = a.get("content", "").strip()
            if key and content:
                self.meta.setdefault(key, []).append(content)
        elif tag == "link" and "image_src" in a.get("rel", "").lower():
            self.image_src = a.get("href") or self.image_src
        elif tag == "title":
            self._in_title = True
        elif tag == "body":
            self.done = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            self.done = True

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def _fetch_head_html(url: str) -> Optional[Tuple[str, str]]:
    """Download just enough of the page to read <head>. Returns (html, final_url)."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype.lower():
                return None
            gz = "gzip" in resp.headers.get("Content-Encoding", "").lower()
            inflater = zlib.decompressobj(16 + zlib.MAX_WBITS) if gz else None
            charset = "utf-8"
            m = re.search(r"charset=([\w\-]+)", ctype, re.I)
            if m:
                charset = m.group(1)

            buf = b""
            while len(buf) < MAX_HEAD_BYTES:
                chunk = resp.read(16384)
                if not chunk:
                    break
                buf += inflater.decompress(chunk) if inflater else chunk
                if b"</head>" in buf.lower():
                    break
            return buf.decode(charset, "ignore"), resp.geturl()
    except Exception as exc:
        print(f"[NewsImages] fetch failed for {url[:80]}: {exc}")
        return None


# ---------------------------------------------------- 3) relevance / validity --
_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "into", "over", "after",
    "before", "about", "are", "was", "were", "has", "have", "had", "will", "its",
    "his", "her", "their", "not", "but", "you", "your", "who", "how", "why",
    "what", "when", "new", "says", "say", "amid", "out", "off", "all", "can",
}


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2 and t not in _STOP}


def _strip_source(title: str) -> str:
    """Google News headlines look like 'Headline - Publisher'."""
    return re.sub(r"\s+[-–—|]\s+[^-–—|]{2,60}$", "", title or "").strip()


def titles_match(feed_title: str, page_title: str) -> bool:
    """True when the page is (very likely) the same story as the RSS headline."""
    a, b = _tokens(_strip_source(feed_title)), _tokens(page_title)
    if not a or not b:
        return True  # nothing to compare; trust the publisher's og:image
    return len(a & b) / min(len(a), len(b)) >= TITLE_OVERLAP_MIN


_BAD_IMAGE_HINT = re.compile(
    r"(?<![a-z])(logo|favicon|sprite|placeholder|default[-_]?(image|og|share|thumb)?|"
    r"no[-_]?image|blank|spacer|pixel|avatar|icon)(?![a-z])",
    re.I,
)


def _is_google_host(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host.endswith(("google.com", "googleusercontent.com", "gstatic.com", "ggpht.com"))


def _clean_image_url(candidate: str, base_url: str) -> Optional[str]:
    if not candidate or candidate.startswith("data:"):
        return None
    url = urljoin(base_url, candidate.strip())
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    if _is_google_host(url):
        return None  # Google News' own logo, not the story's image
    if parsed.path.lower().endswith((".svg", ".ico")):
        return None
    if _BAD_IMAGE_HINT.search(parsed.path):
        return None
    if parsed.scheme == "http":
        url = "https://" + url[len("http://"):]  # avoid mixed-content blocking
    return url


def _pick_image(head: _HeadParser, base_url: str) -> Optional[str]:
    keys = ("og:image:secure_url", "og:image", "og:image:url", "twitter:image", "twitter:image:src")
    candidates: List[str] = []
    for k in keys:
        candidates.extend(head.meta.get(k, []))
    if head.image_src:
        candidates.append(head.image_src)
    for c in candidates:
        cleaned = _clean_image_url(c, base_url)
        if cleaned:
            return cleaned
    return None


def resolve_image(article: Dict[str, Any]) -> Optional[str]:
    """Blocking: full pipeline for one article. Returns a verified image URL or None."""
    page_url = _publisher_url(article.get("url", ""))
    if not page_url:
        return None
    fetched = _fetch_head_html(page_url)
    if not fetched:
        return None
    html_text, final_url = fetched

    head = _HeadParser()
    try:
        head.feed(html_text)
    except Exception:
        pass  # malformed HTML: use whatever was parsed before the error

    page_title = (head.meta.get("og:title") or [head.title.strip()])[0]
    if page_title and not titles_match(article.get("title", ""), page_title):
        print(f"[NewsImages] rejected (different story): {article.get('title','')[:60]!r} vs {page_title[:60]!r}")
        return None
    return _pick_image(head, final_url)


# --------------------------------------------------------- cache + scheduling --
def _cache_get(news_id: str) -> Tuple[bool, Optional[str]]:
    """Returns (is_fresh_entry, url_or_None)."""
    with _lock:
        entry = _cache.get(news_id)
        if entry and entry[0] > time.time():
            return True, entry[1]
        if entry:
            _cache.pop(news_id, None)
    return False, None


def _cache_put(news_id: str, url: Optional[str]) -> None:
    ttl = TTL_FOUND if url else TTL_MISSING
    with _lock:
        _cache[news_id] = (time.time() + ttl, url)
        if len(_cache) > CACHE_LIMIT:  # drop the entries closest to expiry
            for key, _ in sorted(_cache.items(), key=lambda kv: kv[1][0])[: CACHE_LIMIT // 4]:
                _cache.pop(key, None)


def _job(article: Dict[str, Any]) -> Optional[str]:
    news_id = article["news_id"]
    try:
        url = resolve_image(article)
    except Exception as exc:  # never let a worker crash the pool
        print(f"[NewsImages] error for {news_id}: {exc}")
        url = None
    _cache_put(news_id, url)
    with _lock:
        _inflight.pop(news_id, None)
    return url


def _schedule(article: Dict[str, Any]) -> Optional[Future]:
    news_id = article["news_id"]
    fresh, _ = _cache_get(news_id)
    if fresh:
        return None
    with _lock:
        if news_id in _inflight:
            return _inflight[news_id]
        fut = _executor.submit(_job, article)
        _inflight[news_id] = fut
        return fut


# ------------------------------------------------------------------ public API --
def attach_cached_images(articles: Iterable[Dict[str, Any]]) -> None:
    """Set `image_url` on each article from cache (None if unknown). Never blocks."""
    for a in articles:
        if a.get("image_url"):
            continue
        _, url = _cache_get(a["news_id"])
        a["image_url"] = url


def enrich_articles(articles: List[Dict[str, Any]], budget: float = 3.5) -> None:
    """
    Kick off resolution for articles without an image and wait up to `budget`
    seconds. Whatever is still running finishes in the background (and is
    served by `image_state` on the next poll).
    """
    todo = [a for a in articles if not a.get("image_url")]
    futures = [f for f in (_schedule(a) for a in todo) if f is not None]
    if futures and budget > 0:
        wait(futures, timeout=budget)
    attach_cached_images(articles)


def image_state(article: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    ('ready', url)   image found
    ('missing', None) resolved, no usable image (UI keeps its tile)
    ('pending', None) still being resolved
    Starts resolution if it has not been started.
    """
    if article.get("image_url"):  # supplied by the feed itself
        return "ready", article["image_url"]
    fresh, url = _cache_get(article["news_id"])
    if fresh:
        return ("ready", url) if url else ("missing", None)
    _schedule(article)
    return "pending", None
