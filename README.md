# sebzehali.com

Daily wholesale fruit, vegetable and fish prices (hal fiyatları) from Turkish city councils, as a
static website. Python 3 standard library only; no database, no server.

## How it works

1. `python3 -m sebzehali.fetch` downloads each city's bulletin into `data/YYYY/MM/DD/<city>.json`
   (product names normalised so the same product matches across cities).
2. `python3 -m sebzehali.build` turns all of `data/` into a static site in `site/`:
   - `/`: today's overview, popular products, search;
   - `/hal/<city>/`: one city's bulletin with change since the previous one;
   - `/urun/<product>/`: one product across cities, 90-day chart, FAQ (with FAQPage markup);
   - `/hakkinda/`: sources and disclaimer; plus `sitemap.xml`, `robots.txt`, `CNAME`.
3. GitHub Actions (`.github/workflows/daily.yml`) runs both four times a day, commits new data and
   deploys to GitHub Pages.

## Sources

| City | Source | History |
|---|---|---|
| İzmir | open data JSON API (`openapi.izmir.bel.tr`) | any past date |
| Bursa | `bursa.bel.tr/hal_fiyatlari` (HTML) | today only, so history builds up day by day |
| Konya | `konya.bel.tr/hal-fiyatlari?tarih=` (HTML) | ~2,000 past bulletins |

Not yet: İstanbul's open data API (`halfiyatlaripublicdata.ibb.gov.tr`) refused connections when
tested on 2026-10-10. Its website's own request embeds login values in the page; don't reuse those.
Ankara, Antalya and Mersin publish too but need a JavaScript-rendered page or a form; add them as
new modules in `sebzehali/sources/`.

## Adding a city

Create `sebzehali/sources/<city>.py` with `CITY`, `NAME`, `URL`, `HISTORY` and `fetch(date)`
returning `(bulletin_date, rows)`, where each row is
`(name, unit, min, max, avg_or_None, category)` and category is one of `sebze`, `meyve`, `ithal`,
`balik`. Add it to `sources/__init__.py`, save a copy of the page in `tests/fixtures/` and add a
test in `tests/test_sources.py`.

If a product doesn't match across cities, add an alias in `sebzehali/normalize.py`, then run
`python3 -m sebzehali.fetch --renormalize` to re-apply it to stored data.

## Local

```
python3 -m sebzehali.fetch --backfill 60   # first run: 60 days of history where available
python3 -m sebzehali.build --out site
python3 -m http.server -d site 8000
python3 -m unittest discover -s tests -t .
```

## Going live (one-off)

- GitHub repo → Settings → Pages → Source: **GitHub Actions**.
- DNS for sebzehali.com: `www` CNAME → `agilereleaseltd.github.io`; apex A records
  185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 (GitHub Pages redirects the
  apex to www). Then tick "Enforce HTTPS".
- Google Search Console: add the domain, submit `https://www.sebzehali.com/sitemap.xml`.
