import html, json, os, re, urllib.request, xml.etree.ElementTree as ET
from datetime import date, timedelta

FEEDS = {
    "Farnam Street": "https://fs.blog/feed/",
    "Gottman Institute": "https://www.gottman.com/feed/",
    "Greater Good": "https://greatergood.berkeley.edu/site/rss/articles",
    "HBR": "http://feeds.hbr.org/harvardbusiness",
    "MIT Sloan": "https://sloanreview.mit.edu/feed/",
    "McKinsey": "https://www.mckinsey.com/insights/rss",
    "IEEE Spectrum": "https://spectrum.ieee.org/feeds/feed.rss",
    "MD+DI": "https://news.google.com/rss/search?q=site:mddionline.com&hl=en-US&gl=US&ceid=US:en",
    "EE Times": "https://www.eetimes.com/feed/",
    "Aeon": "https://aeon.co/feed.rss",
    "Psyche": "https://psyche.co/feed",
    "Life in Norway": "https://www.lifeinnorway.net/feed/",
}

CATEGORY = {
    "Farnam Street": "Mental Models", "Psyche": "Mental Models",
    "Gottman Institute": "Family", "Greater Good": "Family",
    "HBR": "Strategy", "MIT Sloan": "Strategy", "McKinsey": "Strategy",
    "IEEE Spectrum": "Engineering", "MD+DI": "Engineering", "EE Times": "Engineering",
    "Aeon": "Norway & Ideas", "Life in Norway": "Norway & Ideas",
}

CANDIDATES = "candidates.json"
CONTENT = "content.json"
DECISIONS = "decisions.json"
ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
today = str(date.today())


def clean(text, limit=220):
    """Strip HTML tags and trim to a short summary."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit - 3].rsplit(" ", 1)[0] + "…"


def feed_image(e, raw_html):
    """Find an image in an RSS/Atom entry."""
    for tag in (MEDIA + "content", MEDIA + "thumbnail"):
        for m in e.iter(tag):
            if m.get("url") and m.get("medium", "image") == "image":
                return m.get("url")
    enc = e.find("enclosure")
    if enc is not None and (enc.get("type") or "").startswith("image"):
        return enc.get("url")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', raw_html or "")
    return html.unescape(m.group(1)) if m else ""


def meta_tag(page, name):
    for pat in (r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']%s["\']'):
        m = re.search(pat % re.escape(name), page, re.I)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


# 1. Load candidates, drop removed sources, expire old unreviewed items
items = json.load(open(CANDIDATES)) if os.path.exists(CANDIDATES) else []
items = [i for i in items if i["source"] in FEEDS]
cutoff = str(date.today() - timedelta(days=14))
for i in items:
    if i["status"] == "new" and i["dateAdded"] < cutoff:
        i["status"] = "expired"

# 2. Apply decisions (tolerates several pastes in one file)
dec = {}
if os.path.exists(DECISIONS):
    dec = dict(re.findall(r'"([^"]+)"\s*:\s*"(kept|skipped)"', open(DECISIONS).read()))
print(len(dec), "decisions read")
for i in items:
    choice = dec.get(i["url"])
    if choice and i["status"] == "new":
        i["status"] = choice
        i["decided"] = today

# 3. Fetch feeds: add new candidates, backfill summary/image on known ones
by_url = {i["url"]: i for i in items}
seen_titles = {i["title"] for i in items}
for source, feed in FEEDS.items():
    try:
        req = urllib.request.Request(feed, headers=HEADERS)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
        entries = []
        for e in root.iter("item"):
            body = e.findtext("description") or e.findtext(CONTENT_NS + "encoded") or ""
            entries.append((e.findtext("title"), e.findtext("link"), body, e))
        if not entries:  # Atom feeds
            for e in root.iter(ATOM + "entry"):
                link = e.find(ATOM + "link")
                body = e.findtext(ATOM + "summary") or e.findtext(ATOM + "content") or ""
                entries.append((e.findtext(ATOM + "title"),
                                link.get("href") if link is not None else None, body, e))
        new = 0
        for title, url, body, e in entries:
            if not url or not title:
                continue
            if source == "MD+DI":  # Google News adds " - Site Name" to titles
                title = title.rsplit(" - ", 1)[0]
            summary, image = clean(body), feed_image(e, body)
            if source == "MD+DI":
                summary = ""  # Google News descriptions just repeat the title
            if url in by_url:
                old = by_url[url]
                if not old.get("summary"): old["summary"] = summary
                if not old.get("image"): old["image"] = image
                continue
            if title in seen_titles:
                continue
            item = {"title": title, "url": url, "source": source, "summary": summary,
                    "image": image, "dateAdded": today, "status": "new"}
            items.append(item); by_url[url] = item; seen_titles.add(title); new += 1
        print(f"OK   {source}: {new} new")
    except Exception as ex:
        print(f"FAIL {source}: {ex}")

# 4. Add kept items to content.json; fill gaps from feed data
content = json.load(open(CONTENT))
content_urls = {c["url"] for c in content}
added = 0
for i in items:
    if i["status"] == "kept" and i["url"] not in content_urls:
        content.append({"title": i["title"], "summary": "", "source": i["source"],
                        "author": "", "image": "", "url": i["url"],
                        "category": CATEGORY.get(i["source"], ""), "type": "Curated Link",
                        "readTime": "", "dateAdded": today})
        content_urls.add(i["url"])
        added += 1
filled = 0
for c in content:
    cand = by_url.get(c["url"])
    if not cand:
        continue
    before = (c.get("summary"), c.get("image"))
    c["summary"] = c.get("summary") or cand.get("summary", "")
    c["image"] = c.get("image") or cand.get("image", "")
    filled += before != (c["summary"], c["image"])
print(added, "added to content.json;", filled, "filled from feeds")

# 5. Still missing an image? Try the article page once (og: tags)
enriched = 0
for c in content:
    if c.get("image") or c.get("checked"):
        continue
    c["checked"] = True
    try:
        req = urllib.request.Request(c["url"], headers={**HEADERS, "Accept": "text/html"})
        page = urllib.request.urlopen(req, timeout=15).read(400000).decode("utf-8", "ignore")
    except Exception:
        continue
    c["image"] = meta_tag(page, "og:image")
    if not c.get("summary"):
        c["summary"] = clean(meta_tag(page, "og:description") or meta_tag(page, "description"))
    enriched += 1
print(enriched, "enriched from article pages")

# 6. Save everything at the end
json.dump(items, open(CANDIDATES, "w"), indent=2)
json.dump(content, open(CONTENT, "w"), indent=2)
json.dump({}, open(DECISIONS, "w"))
print(len(items), "candidates total")
