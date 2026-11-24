import json, os, urllib.request, xml.etree.ElementTree as ET
from datetime import date

FEEDS = {"Farnam Street": "https://fs.blog/feed/"}
FILE = "candidates.json"

items = json.load(open(FILE)) if os.path.exists(FILE) else []
seen = {i["url"] for i in items}

for source, feed in FEEDS.items():
    req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
    for it in ET.fromstring(urllib.request.urlopen(req).read()).iter("item"):
        url = it.findtext("link")
        if url in seen: continue
        items.append({"title": it.findtext("title"), "url": url,
                      "source": source, "dateAdded": str(date.today()),
                      "status": "new"})
        seen.add(url)

json.dump(items, open(FILE, "w"), indent=2)
print(len(items), "candidates")
