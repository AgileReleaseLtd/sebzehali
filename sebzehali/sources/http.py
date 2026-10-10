import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; sebzehali.com price bot; +https://www.sebzehali.com/hakkinda/)"
_last = [0.0]


def get(url, timeout=40, tries=3):
    """GET with a polite 1 s gap between requests and a few retries."""
    err = None
    for attempt in range(tries):
        wait = 1.0 - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = e
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {err}")
