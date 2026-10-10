"""Bursa Büyükşehir Belediyesi hal page: today's bulletin only, fruit/veg and fish tabs."""

import re

from .html_table import tables
from .http import get

CITY = "bursa"
NAME = "Bursa"
URL = "https://www.bursa.bel.tr/hal_fiyatlari"
HISTORY = False

# Tab order on the page: Meyve, Sebze, İthal, then six seafood tabs.
_TAB_CATEGORY = ["meyve", "sebze", "ithal", "balik", "balik", "balik", "balik", "balik", "balik"]


def fetch(date):
    page = get(URL)
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})\s*Tarihli", page)
    if not m:
        return None
    bulletin = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    rows = []
    for i, t in enumerate(tables(page)):
        cat = _TAB_CATEGORY[i] if i < len(_TAB_CATEGORY) else "balik"
        for cells in t:
            if len(cells) < 3 or cells[0].upper().startswith("ÜRÜN"):
                continue
            prices = re.findall(r"[\d.,]+", cells[2])
            if not prices:
                continue
            low, high = prices[0], prices[-1]
            rows.append((cells[0], cells[1].strip("()"), low, high, None, cat))
    return (bulletin, rows) if rows else None
