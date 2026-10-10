"""İzmir Büyükşehir Belediyesi open data API (JSON, any past date)."""

import json

from .http import get

CITY = "izmir"
NAME = "İzmir"
URL = "https://acikveri.bizizmir.com/"
API = "https://openapi.izmir.bel.tr/api/ibb/halfiyatlari/sebzemeyve/{date}"
_CATEGORY = {"SEBZE": "sebze", "MEYVE": "meyve", "İTHAL": "ithal", "ITHAL": "ithal"}
HISTORY = True


def fetch(date):
    data = json.loads(get(API.format(date=date)) or "null")
    if not data or not data.get("HalFiyatListesi"):
        return None
    bulletin = (data.get("BultenTarihi") or date)[:10]
    rows = [
        (x["MalAdi"], x.get("Birim"), x.get("AsgariUcret"), x.get("AzamiUcret"), x.get("OrtalamaUcret"),
         _CATEGORY.get((x.get("MalTipAdi") or "").upper(), "sebze"))
        for x in data["HalFiyatListesi"]
    ]
    return bulletin, rows
