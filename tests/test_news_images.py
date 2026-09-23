import base64, time, sys
sys.path.insert(0, ".")
from src.data import news_images as ni

# 1) legacy Google News id (base64 protobuf-ish wrapper around the real URL)
real = "https://www.thehindu.com/news/national/some-story/article12345.ece"
payload = b"\x08\x13\x22" + bytes([len(real)]) + real.encode() + b"\xd2\x01\x00"
tok = base64.urlsafe_b64encode(payload).decode().rstrip("=")
gurl = f"https://news.google.com/rss/articles/{tok}?oc=5"
assert ni._legacy_decode(gurl) == real, ni._legacy_decode(gurl)
# new-format token has no plain URL inside -> must return None (falls to decoder lib)
new_tok = base64.urlsafe_b64encode(b"\x08\x13\x22\x5aAU_yqLPzXabc123def").decode().rstrip("=")
assert ni._legacy_decode(f"https://news.google.com/rss/articles/{new_tok}") is None
# non-google links pass straight through
assert ni._publisher_url("https://example.com/a") == "https://example.com/a"
print("1 decode OK")

# 2) parser
html = """<html><head><title>Fallback Title</title>
<meta property="og:title" content="Cabinet approves new metro line for Pune">
<meta property="og:image" content="/media/metro.jpg">
<meta name="twitter:image" content="https://cdn.x.com/tw.jpg">
</head><body><meta property="og:image" content="https://evil/late.jpg"></body></html>"""
h = ni._HeadParser(); h.feed(html)
assert h.meta["og:title"] == ["Cabinet approves new metro line for Pune"]
assert "https://evil/late.jpg" not in h.meta.get("og:image", []), "body meta must be ignored"
assert ni._pick_image(h, "https://site.com/news/1") == "https://site.com/media/metro.jpg"
print("2 parse OK")

# 3) image filter
c = ni._clean_image_url
assert c("https://lh3.googleusercontent.com/abc=s0-w300", "https://x.com") is None
assert c("https://news.google.com/logo.png", "https://x.com") is None
assert c("https://x.com/static/site-logo.png", "https://x.com") is None
assert c("https://x.com/img/technology/photo.jpg", "https://x.com") == "https://x.com/img/technology/photo.jpg"  # 'technology' must NOT trip 'logo'
assert c("http://x.com/a.jpg", "https://x.com") == "https://x.com/a.jpg"
assert c("data:image/png;base64,AAA", "https://x.com") is None
assert c("https://x.com/a.svg", "https://x.com") is None
print("3 filter OK")

# 4) relevance guard
feed = "Cabinet approves Pune metro extension to Hinjewadi - The Hindu"
assert ni.titles_match(feed, "Cabinet approves new metro line for Pune | The Hindu") is True
assert ni.titles_match(feed, "The Hindu - Latest news, breaking news") is False        # generic landing page
assert ni.titles_match(feed, "IPL 2026: Mumbai beat Chennai by 5 wickets") is False    # different story
assert ni.titles_match(feed, "") is True
print("4 relevance OK")

# 5) pipeline w/ mocked network: match accepted, mismatch rejected, failure -> None, caching + inflight
calls = {"n": 0}
def fake_fetch(url):
    calls["n"] += 1; time.sleep(0.2)
    if "good" in url:  return (html, url)
    if "wrong" in url: return ("<head><meta property='og:title' content='Totally unrelated cricket news'><meta property='og:image' content='https://x.com/c.jpg'></head>", url)
    return None
ni._fetch_head_html = fake_fetch
A = [
  {"news_id":"L1","title":"Cabinet approves new metro line for Pune - The Hindu","url":"https://good.com/a"},
  {"news_id":"L2","title":"Cabinet approves new metro line for Pune - The Hindu","url":"https://wrong.com/a"},
  {"news_id":"L3","title":"Cabinet approves new metro line for Pune - The Hindu","url":"https://down.com/a"},
]
t=time.time(); ni.enrich_articles(A, budget=5); dt=time.time()-t
assert A[0]["image_url"]=="https://good.com/media/metro.jpg", A[0]
assert A[1]["image_url"] is None and A[2]["image_url"] is None
assert dt < 1.0, f"should run in parallel, took {dt}"
n=calls["n"]; ni.enrich_articles(A, budget=5); assert calls["n"]==n, "cache must prevent refetch"
assert ni.image_state(A[0])==("ready","https://good.com/media/metro.jpg")
assert ni.image_state(A[1])==("missing",None)
print("5 pipeline OK  (parallel %.2fs)"%dt)

# 6) budget expiry -> still resolves in background, image_state reports pending then ready
ni._cache.clear()
def slow(url): time.sleep(1.0); return (html,url)
ni._fetch_head_html = slow
B=[{"news_id":"S1","title":"Cabinet approves new metro line for Pune","url":"https://good.com/s"}]
ni.enrich_articles(B, budget=0.1)
assert B[0]["image_url"] is None and ni.image_state(B[0])[0]=="pending"
time.sleep(1.3)
assert ni.image_state(B[0])[0]=="ready"
print("6 background OK")
print("ALL PASSED")
