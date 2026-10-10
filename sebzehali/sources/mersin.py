"""Mersin Büyükşehir Belediyesi: a form POST per category and date (any past date).

The table lists every branch market (şube) and both conventional and "iyi tarım" produce; only the
central market's conventional rows are kept, so each product appears once like the other cities.
"""

import urllib.parse

from ..normalize import slugify

from .html_table import tables
from .http import get

CITY = "mersin"
NAME = "Mersin"
URL = "https://www.mersin.bel.tr/hal-fiyatlari"
HISTORY = True
_ENDPOINT = "https://www.mersin.bel.tr/hal-fiyatlari-day"
_CATEGORIES = {"4": "sebze", "3": "meyve"}


def fetch(date):
    rows = []
    for code, cat in _CATEGORIES.items():
        body = urllib.parse.urlencode({"published": date, "product_category": code}).encode()
        page = get(_ENDPOINT, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        rows += parse(page, cat)
    return (date, rows) if rows else None


def parse(page, cat):
    out, seen = [], set()
    for t in tables(page):
        for cells in t:
            if len(cells) < 8 or cells[0].upper() != "MERKEZ" or not cells[3].upper().startswith("GELENEKSEL"):
                continue
            product, kind = cells[1], cells[2]
            same = slugify(kind).replace("-", "") in (slugify(product).replace("-", ""), "diger")
            name = product if same else f"{product} ({kind})"
            if name in seen:
                continue
            seen.add(name)
            out.append((name, cells[7], cells[4], cells[5], cells[6], cat))
    return out
