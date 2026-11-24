# build_content.py

import feedparser

RSS_FEED = "https://fs.blog/feed/"

feed = feedparser.parse(RSS_FEED)

print(f"\nFeed: {feed.feed.title}\n")

for entry in feed.entries[:10]:
    print(f"Title: {entry.title}")
    print(f"URL:   {entry.link}")
    print("-" * 60)
