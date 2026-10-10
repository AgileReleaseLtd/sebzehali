import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; sebzehali.com price bot; +https://www.sebzehali.com/hakkinda/)"
_last = [0.0]


def get(url, timeout=40, tries=3, data=None, headers=None, raw=False):
    """GET (or POST when data is given) with a polite 1 s gap between requests and a few retries.
    Returns text, or bytes when raw=True."""
    err = None
    for attempt in range(tries):
        wait = 1.0 - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()
        try:
            h = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9", **(headers or {})}
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                return body if raw else body.decode(r.headers.get_content_charset() or "utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = e
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {err}")
