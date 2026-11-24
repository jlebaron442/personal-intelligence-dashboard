import urllib.request, xml.etree.ElementTree as ET

feed = "https://fs.blog/feed/"
req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
xml = urllib.request.urlopen(req).read()
for item in ET.fromstring(xml).iter("item"):
    print(item.findtext("title"))
