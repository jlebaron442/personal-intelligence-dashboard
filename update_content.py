import json, os, urllib.request, xml.etree.ElementTree as ET
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
FILE = "candidates.json"
ATOM = "{http://www.w3.org/2005/Atom}"

items = json.load(open(FILE)) if os.path.exists(FILE) else []
items = [i for i in items if i["source"] in FEEDS]
cutoff = str(date.today() - timedelta(days=14))
for i in items:
    if i["status"] == "new" and i["dateAdded"] < cutoff:
        i["status"] = "expired"
CATEGORY = {"Farnam Street": "Mental Models", "Psyche": "Mental Models",
            "Gottman Institute": "Family", "Greater Good": "Family",
            "HBR": "Strategy", "MIT Sloan": "Strategy", "McKinsey": "Strategy",
            "IEEE Spectrum": "Engineering", "MD+DI": "Engineering", "EE Times": "Engineering",
            "Aeon": "Norway & Ideas", "Life in Norway": "Norway & Ideas"}

dec = json.load(open("decisions.json")) if os.path.exists("decisions.json") else {}
content = json.load(open("content.json"))
for i in items:
    choice = dec.get(i["url"])
    if not choice or i["status"] != "new": continue
    i["status"] = choice
    if choice == "kept":
        content.append({"title": i["title"], "summary": "", "source": i["source"],
                        "author": "", "image": "", "url": i["url"],
                        "category": CATEGORY.get(i["source"], ""), "type": "Curated Link",
                        "readTime": "", "dateAdded": str(date.today())})
json.dump(content, open("content.json", "w"), indent=2)
json.dump({}, open("decisions.json", "w"))
seen = {i["url"] for i in items}

for source, feed in FEEDS.items():
    try:
        req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "application/rss+xml, application/xml, text/xml, */*"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
        entries = [(e.findtext("title"), e.findtext("link")) for e in root.iter("item")]
        if not entries:  # Atom feeds
            entries = [(e.findtext(ATOM + "title"),
                        (e.find(ATOM + "link").get("href") if e.find(ATOM + "link") is not None else None))
                       for e in root.iter(ATOM + "entry")]
        new = 0
        for title, url in entries:
            if not url or url in seen: continue
            items.append({"title": title, "url": url, "source": source,
                          "dateAdded": str(date.today()), "status": "new"})
            seen.add(url); new += 1
        print(f"OK   {source}: {new} new")
    except Exception as e:
        print(f"FAIL {source}: {e}")

json.dump(items, open(FILE, "w"), indent=2)
print(len(items), "candidates total")
