import json, os, urllib.request, xml.etree.ElementTree as ET
from datetime import date

FEEDS = {
    "Farnam Street": "https://fs.blog/feed/",
    "Gottman Institute": "https://www.gottman.com/feed/",
    "Greater Good": "https://greatergood.berkeley.edu/site/rss/articles",
    "HBR": "http://feeds.hbr.org/harvardbusiness",
    "MIT Sloan": "https://sloanreview.mit.edu/feed/",
    "McKinsey": "https://www.mckinsey.com/insights/rss",
    "IEEE Spectrum": "https://spectrum.ieee.org/feeds/feed.rss",
    "MD+DI": "https://www.mddionline.com/rss.xml",
    "EE Times": "https://www.eetimes.com/feed/",
    "Aeon": "https://aeon.co/feed.rss",
    "Psyche": "https://psyche.co/feed",
    "NRK": "https://www.nrk.no/toppsaker.rss",
    "Bergens Tidende": "https://www.bt.no/rss",
}
FILE = "candidates.json"
ATOM = "{http://www.w3.org/2005/Atom}"

items = json.load(open(FILE)) if os.path.exists(FILE) else []
seen = {i["url"] for i in items}

for source, feed in FEEDS.items():
    try:
        req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
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
