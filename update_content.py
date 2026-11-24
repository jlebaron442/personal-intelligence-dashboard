import urllib.request, xml.etree.ElementTree as ET

feed = "https://fs.blog/feed/"
xml = urllib.request.urlopen(feed).read()
for item in ET.fromstring(xml).iter("item"):
    print(item.findtext("title"))
