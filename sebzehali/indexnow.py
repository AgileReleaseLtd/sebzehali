"""Tell IndexNow search engines (Bing, Yandex, Seznam, Naver) which pages changed.

    python3 -m sebzehali.indexnow site/sitemap.xml

Called by the workflow after a scheduled deploy; every page shows the day's prices, so the whole
sitemap is sent. The key file static/<KEY>.txt proves the site is ours; keep it published.
"""

import json
import re
import sys
import urllib.request

KEY = "8720afce7ece8827ca77088cfbfe6054"
HOST = "www.sebzehali.com"


def main(sitemap):
    urls = re.findall(r"<loc>([^<]+)</loc>", open(sitemap, encoding="utf-8").read())
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: {len(urls)} URLs, HTTP {r.status}")
    except urllib.error.HTTPError as e:
        # 202 = accepted, key not checked yet; anything else is logged but never fails the deploy.
        print(f"IndexNow: {len(urls)} URLs, HTTP {e.code} {e.read()[:200]!r}")


if __name__ == "__main__":
    main(sys.argv[1])
