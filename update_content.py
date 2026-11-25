import json, os, re, urllib.request, xml.etree.ElementTree as ET
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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}
today = str(date.today())

# 1. Load candidates, drop removed sources, expire old unreviewed items
items = json.load(open(CANDIDATES)) if os.path.exists(CANDIDATES) else []
items = [i for i in items if i["source"] in FEEDS]
cutoff = str(date.today() - timedelta(days=14))
for i in items:
    if i["status"] == "new" and i["dateAdded"] < cutoff:
        i["status"] = "expired"

# 2. Read decisions (tolerates several pastes in one file)
dec = {}
if os.path.exists(DECISIONS):
    raw = open(DECISIONS).read()
    dec = dict(re.findall(r'"([^"]+)"\s*:\s*"(kept|skipped)"', raw))
print(len(dec), "decisions read")

# 3. Apply decisions; add kept items to content.json
content = json.load(open(CONTENT))
content_urls = {c["url"] for c in content}
added = 0
for i in items:
    choice = dec.get(i["url"])
    if choice and i["status"] == "new":
        i["status"] = choice
        i["decided"] = today
    if i["status"] == "kept" and i["url"] not in content_urls:
        content.append({"title": i["title"], "summary": "", "source": i["source"],
                        "author": "", "image": "", "url": i["url"],
                        "category": CATEGORY.get(i["source"], ""), "type": "Curated Link",
                        "readTime": "", "dateAdded": today})
        content_urls.add(i["url"])
        added += 1
print(added, "added to content.json")

# 4. Fetch feeds for new candidates
seen_urls = {i["url"] for i in items}
seen_titles = {i["title"] for i in items}
for source, feed in FEEDS.items():
    try:
        req = urllib.request.Request(feed, headers=HEADERS)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
        entries = [(e.findtext("title"), e.findtext("link")) for e in root.iter("item")]
        if not entries:  # Atom feeds
            entries = []
            for e in root.iter(ATOM + "entry"):
                link = e.find(ATOM + "link")
                entries.append((e.findtext(ATOM + "title"),
                                link.get("href") if link is not None else None))
        new = 0
        for title, url in entries:
            if not url or not title:
                continue
            if source == "MD+DI":  # Google News adds " - Site Name" to titles
                title = title.rsplit(" - ", 1)[0]
            if url in seen_urls or title in seen_titles:
                continue
            items.append({"title": title, "url": url, "source": source,
                          "dateAdded": today, "status": "new"})
            seen_urls.add(url); seen_titles.add(title); new += 1
        print(f"OK   {source}: {new} new")
    except Exception as e:
        print(f"FAIL {source}: {e}")

# 5. Save everything at the end
json.dump(items, open(CANDIDATES, "w"), indent=2)
json.dump(content, open(CONTENT, "w"), indent=2)
json.dump({}, open(DECISIONS, "w"))
print(len(items), "candidates total")
