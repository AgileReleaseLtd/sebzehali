"""Build the static site from data/ into site/.

    python3 -m sebzehali.build [--out site] [--base-url https://www.sebzehali.com]

Pages: / (today's overview), /hal/<city>/ (one city's bulletin), /urun/<product>/ (one product
across cities, with a price chart), /hakkinda/ (sources), plus sitemap.xml and robots.txt.
No JavaScript framework; the only script is the search filter on the home page.
"""

import argparse
import collections
import datetime as dt
import html
import json
import pathlib
import shutil
import statistics

from . import normalize, sources

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STATIC = ROOT / "static"

CITY_NAMES = {m.CITY: m.NAME for m in sources.ALL}
CITY_URLS = {m.CITY: m.URL for m in sources.ALL}
CITY_COLORS = {"izmir": "#1f7a4d", "bursa": "#c2410c", "konya": "#1d4ed8"}
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
FEATURED = ["domates", "biber", "patates", "sogan", "salatalik", "patlican", "elma", "limon", "muz", "portakal",
            "mandalina", "uzum", "havuc", "kabak", "fasulye", "marul"]
RECENT_DAYS = 21  # products not seen in this many days get no page

e = html.escape


def tr_date(iso, weekday=False):
    d = dt.date.fromisoformat(iso)
    s = f"{d.day} {MONTHS[d.month - 1]} {d.year}"
    if weekday:
        s += " " + ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][d.weekday()]
    return s


def money(v):
    if v is None:
        return "–"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return (s[:-3] if s.endswith(",00") else s) + " ₺"


def mid(item):
    return item["avg"] if item.get("avg") else (item["min"] + item["max"]) / 2


# ---------------------------------------------------------------- data

def load():
    """{city: {date: [items]}} for every stored bulletin."""
    out = collections.defaultdict(dict)
    for p in sorted(DATA.glob("*/*/*/*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        out[doc["city"]][doc["date"]] = doc["items"]
    return out


class Site:
    def __init__(self, data, base_url):
        self.data = data
        self.base = base_url.rstrip("/")
        self.latest = {c: max(days) for c, days in data.items() if days}
        self.newest = max(self.latest.values())
        cutoff = (dt.date.fromisoformat(self.newest) - dt.timedelta(days=RECENT_DAYS)).isoformat()
        self.cities = sorted((c for c in self.latest if self.latest[c] >= cutoff), key=lambda c: CITY_NAMES.get(c, c))

        # product -> {city: [items in that city's latest bulletin]}
        self.products = collections.defaultdict(lambda: collections.defaultdict(list))
        self.raw_names = collections.defaultdict(list)
        self.category = {}
        for c in self.cities:
            for it in data[c][self.latest[c]]:
                self.products[it["product"]][c].append(it)
                self.raw_names[it["product"]].append(it["raw"])
                self.category.setdefault(it["product"], it["category"])

    def name(self, product):
        return normalize.product_name(product, self.raw_names.get(product, ()))

    def previous(self, city, date):
        earlier = [d for d in self.data[city] if d < date]
        return self.data[city][max(earlier)] if earlier else None

    def series(self, city, product):
        """(unit, [(date, median price)]): the median across the product's varieties in that city's
        most common unit, per bulletin. One line per city, comparable between cities."""
        units = collections.Counter(it["unit"] for items in self.data[city].values()
                                    for it in items if it["product"] == product)
        if not units:
            return None, []
        unit = max(units, key=lambda u: (units[u], u == "kg"))
        pts = []
        for d in sorted(self.data[city]):
            mids = [mid(it) for it in self.data[city][d] if it["product"] == product and it["unit"] == unit]
            if mids:
                pts.append((d, statistics.median(mids)))
        return unit, pts


# ---------------------------------------------------------------- page shell

def page(site, path, title, description, body, extra_head=""):
    canonical = f"{site.base}{path}"
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#1f7a4d">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/style.css">
{extra_head}</head>
<body>
<header class="top"><div class="wrap">
<a class="logo" href="/"><span class="leaf">🥬</span> sebzehali<span class="tld">.com</span></a>
<nav>{''.join(f'<a href="/hal/{c}/">{e(CITY_NAMES[c])}</a>' for c in site.cities)}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
<p>Fiyatlar belediyelerin yayımladığı günlük hal bültenlerinden alınır; toptan (hal) fiyatlarıdır, market ve pazar fiyatları farklıdır.
<a href="/hakkinda/">Kaynaklar ve açıklama</a></p>
<p>© {dt.date.today().year} sebzehali.com</p>
</div></footer>
</body>
</html>
"""


def change_badge(now, before):
    if before is None or not before:
        return ""
    pct = (now - before) / before * 100
    if abs(pct) < 0.5:
        return '<span class="chg flat">=</span>'
    cls, arrow = ("up", "▲") if pct > 0 else ("down", "▼")
    return f'<span class="chg {cls}">{arrow} %{abs(pct):.0f}</span>'


def price_table(rows, show_city=False, prev=None):
    """rows: list of (city, item). prev: {(product, variety, unit): item} for change badges."""
    head = "<th>Şehir</th>" if show_city else "<th>Ürün</th>"
    out = [f'<table class="prices"><thead><tr>{head}<th>Çeşit</th><th>Birim</th><th class="n">En düşük</th>'
           f'<th class="n">En yüksek</th><th class="n">Değişim</th></tr></thead><tbody>']
    for city, it in rows:
        before = prev.get((city, it["product"], it["variety"], it["unit"])) if prev else None
        first = (f'<a href="/hal/{city}/">{e(CITY_NAMES[city])}</a>' if show_city
                 else f'<a href="/urun/{it["product"]}/">{e(normalize.product_name(it["product"], [it["raw"]]))}</a>')
        out.append(
            f'<tr data-q="{e(normalize.slugify(it["raw"]).replace("-", " "))}"><td>{first}</td><td>{e(it["variety"]) or "–"}</td>'
            f'<td>{e(it["unit"])}</td><td class="n">{money(it["min"])}</td><td class="n">{money(it["max"])}</td>'
            f'<td class="n">{change_badge(mid(it), mid(before) if before else None)}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


# ---------------------------------------------------------------- pages

def home(site):
    cards = []
    for p in FEATURED:
        if p not in site.products:
            continue
        lows = [it["min"] for items in site.products[p].values() for it in items if it["unit"] == "kg"]
        highs = [it["max"] for items in site.products[p].values() for it in items if it["unit"] == "kg"]
        if not lows:
            continue
        cards.append(f'<a class="card" href="/urun/{p}/"><b>{e(site.name(p))}</b>'
                     f'<span>{money(min(lows))} – {money(max(highs))}</span><small>kg, {len(site.products[p])} hal</small></a>')

    city_cards = "".join(
        f'<a class="city" href="/hal/{c}/"><b>{e(CITY_NAMES[c])} hal fiyatları</b>'
        f'<small>{tr_date(site.latest[c], True)} bülteni · {len(site.data[c][site.latest[c]])} ürün</small></a>'
        for c in site.cities)

    all_rows = sorted(((c, it) for p in site.products for c, items in site.products[p].items() for it in items),
                      key=lambda r: (normalize.slugify(site.name(r[1]["product"])), r[1]["variety"], r[0]))
    body = f"""
<section class="hero">
<h1>Bugünkü hal fiyatları</h1>
<p>{', '.join(CITY_NAMES[c] for c in site.cities)} hallerinde sebze, meyve{' ve balık' if any(site.category.get(p) == 'balik' for p in site.products) else ''} toptan fiyatları.
Son bülten: <b>{tr_date(site.newest, True)}</b>.</p>
</section>
<section><h2>Çok aranan ürünler</h2><div class="cards">{''.join(cards)}</div></section>
<section><h2>Şehirler</h2><div class="cities">{city_cards}</div></section>
<section>
<h2>Tüm ürünler</h2>
<input id="q" type="search" placeholder="Ürün ara: domates, elma, hamsi…" autocomplete="off" aria-label="Ürün ara">
{price_table(all_rows, show_city=False)}
</section>
<script>
(function(){{var q=document.getElementById('q'),rows=document.querySelectorAll('table.prices tbody tr');
var A={{'ç':'c','ğ':'g','ı':'i','i̇':'i','ö':'o','ş':'s','ü':'u'}};
function n(s){{return s.toLocaleLowerCase('tr').replace(/[çğıöşü]/g,function(c){{return A[c]}}).trim()}}
q.addEventListener('input',function(){{var v=n(q.value);rows.forEach(function(r){{r.style.display=!v||r.dataset.q.indexOf(v)>=0?'':'none'}})}});}})();
</script>"""
    title = f"Hal Fiyatları Bugün – {', '.join(CITY_NAMES[c] for c in site.cities)} Sebze Meyve Fiyatları"
    desc = (f"Güncel hal fiyatları: {tr_date(site.newest)} tarihli {', '.join(CITY_NAMES[c] for c in site.cities)} "
            "hal bültenlerinden domates, biber, patates, soğan ve tüm sebze meyve toptan fiyatları.")
    return page(site, "/", title, desc, body)


def city_page(site, c):
    date = site.latest[c]
    items = site.data[c][date]
    prev_items = site.previous(c, date) or []
    prev = {(c, i["product"], i["variety"], i["unit"]): i for i in prev_items}
    sections = []
    for cat, label in normalize.CATEGORIES.items():
        rows = [(c, it) for it in items if it["category"] == cat]
        if rows:
            rows.sort(key=lambda r: (normalize.slugify(site.name(r[1]["product"])), normalize.slugify(r[1]["variety"])))
            sections.append(f"<h2>{e(label)}</h2>{price_table(rows, prev=prev)}")
    history = sorted(site.data[c], reverse=True)[:10]
    body = f"""
<nav class="crumbs"><a href="/">Hal fiyatları</a> › {e(CITY_NAMES[c])}</nav>
<h1>{e(CITY_NAMES[c])} hal fiyatları</h1>
<p class="lead">{tr_date(date, True)} tarihli {e(CITY_NAMES[c])} hal bülteni: {len(items)} ürün.
Değişim, bir önceki bültene ({tr_date(max(d for d in site.data[c] if d < date)) if prev_items else '–'}) göre ortalama fiyattaki farktır.</p>
{''.join(sections)}
<p class="src">Kaynak: <a href="{e(CITY_URLS[c])}" rel="nofollow noopener">{e(CITY_NAMES[c])} Büyükşehir Belediyesi</a>.
Kayıtlı bültenler: {', '.join(tr_date(d) for d in history)}{' …' if len(site.data[c]) > 10 else ''}</p>"""
    title = f"{CITY_NAMES[c]} Hal Fiyatları Bugün ({tr_date(date)}) – Sebze Meyve Fiyatları"
    desc = f"{CITY_NAMES[c]} hal fiyatları {tr_date(date)}: {len(items)} sebze ve meyvenin en düşük ve en yüksek toptan fiyatı, dünkü fiyatlarla karşılaştırma."
    return page(site, f"/hal/{c}/", title, desc, body)


def chart(site, product):
    lines, legend, all_pts = [], [], []
    for c in site.cities:
        unit, pts = site.series(c, product)
        pts = [p for p in pts if p[0] >= (dt.date.fromisoformat(site.newest) - dt.timedelta(days=90)).isoformat()]
        if len(pts) >= 2:
            lines.append((c, unit, pts))
            all_pts += pts
    if not lines:
        return ""
    W, H, L, R, T, B = 720, 280, 56, 12, 12, 28
    d0 = min(dt.date.fromisoformat(p[0]) for p in all_pts)
    d1 = max(dt.date.fromisoformat(p[0]) for p in all_pts)
    span = max((d1 - d0).days, 1)
    vmax = max(p[1] for p in all_pts) * 1.1
    vmin = 0
    x = lambda d: L + (dt.date.fromisoformat(d) - d0).days / span * (W - L - R)
    y = lambda v: T + (1 - (v - vmin) / (vmax - vmin)) * (H - T - B)
    svg = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(site.name(product))} fiyat grafiği" class="chart">']
    for i in range(5):
        v = vmin + (vmax - vmin) * i / 4
        svg.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>'
                   f'<text x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{v:.0f}</text>')
    for d in (d0, d0 + (d1 - d0) / 2, d1):
        svg.append(f'<text x="{x(d.isoformat()):.1f}" y="{H - 8}" text-anchor="middle">{d.day} {MONTHS[d.month - 1][:3]}</text>')
    for c, unit, pts in lines:
        col = CITY_COLORS.get(c, "#555")
        poly = " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in pts)
        svg.append(f'<polyline points="{poly}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round"/>')
        lx, ly = pts[-1]
        svg.append(f'<circle cx="{x(lx):.1f}" cy="{y(ly):.1f}" r="3.5" fill="{col}"/>')
        legend.append(f'<span><i style="background:{col}"></i>{e(CITY_NAMES[c])} ({e(unit)})</span>')
    svg.append("</svg>")
    return (f'<figure class="chartbox">{"".join(svg)}<figcaption>Tüm çeşitlerin ortanca toptan fiyatı (₺), son 90 gün. '
            f'{"".join(legend)}</figcaption></figure>')


def product_page(site, product):
    name = site.name(product)
    rows = sorted(((c, it) for c, items in site.products[product].items() for it in items),
                  key=lambda r: (normalize.slugify(CITY_NAMES[r[0]]), normalize.slugify(r[1]["variety"])))
    prev = {}
    for c in site.products[product]:
        for it in site.previous(c, site.latest[c]) or []:
            if it["product"] == product:
                prev[(c, it["product"], it["variety"], it["unit"])] = it
    kg = [it for _, it in rows if it["unit"] == "kg"] or [it for _, it in rows]
    lo, hi = min(i["min"] for i in kg), max(i["max"] for i in kg)
    unit = kg[0]["unit"]
    med = statistics.median(mid(i) for i in kg)
    cities = sorted({c for c, _ in rows}, key=lambda c: CITY_NAMES[c])
    city_txt = ", ".join(CITY_NAMES[c] for c in cities)
    cheapest = min(rows, key=lambda r: r[1]["min"] if r[1]["unit"] == unit else 1e12)
    faq = [
        (f"{name} hal fiyatı ne kadar?",
         f"{tr_date(site.newest)} itibarıyla {city_txt} hallerinde {name.lower()} {unit} fiyatı {money(lo)} ile {money(hi)} arasında; "
         f"orta değer yaklaşık {money(med)}."),
        (f"{name} en ucuz hangi halde?",
         f"Son bültenlerde en düşük {name.lower()} fiyatı {CITY_NAMES[cheapest[0]]} halinde: "
         f"{money(cheapest[1]['min'])} / {cheapest[1]['unit']}{' (' + cheapest[1]['variety'].lower() + ')' if cheapest[1]['variety'] else ''}."),
        ("Hal fiyatı ile market fiyatı neden farklı?",
         "Hal fiyatı üreticinin ve komisyoncunun toptan satış fiyatıdır. Markete ve pazara gelene kadar nakliye, "
         "fire, işçilik ve kâr eklendiği için perakende fiyat genellikle daha yüksektir."),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
        ensure_ascii=False)
    related = [p for p in sorted(site.products, key=lambda p: site.name(p))
               if p != product and site.category.get(p) == site.category.get(product)][:24]
    body = f"""
<nav class="crumbs"><a href="/">Hal fiyatları</a> › {e(name)}</nav>
<h1>{e(name)} hal fiyatı bugün</h1>
<p class="lead">{e(name)} toptan fiyatı {city_txt} hallerinde <b>{money(lo)} – {money(hi)}</b> / {e(unit)}
({tr_date(site.newest)}).</p>
{price_table(rows, show_city=True, prev=prev)}
{chart(site, product)}
<section class="faq"><h2>Sık sorulanlar</h2>{faq_html}</section>
<section><h2>Diğer {e(normalize.CATEGORIES.get(site.category.get(product), 'ürün').lower())} fiyatları</h2>
<p class="tags">{''.join(f'<a href="/urun/{p}/">{e(site.name(p))}</a>' for p in related)}</p></section>"""
    title = f"{name} Hal Fiyatı Bugün ({tr_date(site.newest)}) – {city_txt}"
    desc = (f"{name} hal fiyatı: {city_txt} hallerinde {unit} fiyatı {money(lo)} – {money(hi)}. "
            f"Şehir şehir güncel {name.lower()} toptan fiyatları ve 90 günlük fiyat grafiği.")
    return page(site, f"/urun/{product}/", title, desc, body,
                extra_head=f'<script type="application/ld+json">{ld}</script>\n')


def about_page(site):
    srcs = "".join(f'<li><b>{e(m.NAME)}</b>: <a href="{e(m.URL)}" rel="nofollow noopener">{e(m.URL)}</a></li>'
                   for m in sources.ALL)
    body = f"""
<h1>Kaynaklar ve açıklama</h1>
<p>sebzehali.com, büyükşehir belediyelerinin her gün yayımladığı hal fiyat bültenlerini tek yerde toplar.
Fiyatlar her gün birkaç kez otomatik olarak güncellenir.</p>
<h2>Kaynaklar</h2><ul>{srcs}</ul>
<h2>Fiyatlar hakkında</h2>
<ul>
<li>Fiyatlar <b>toptan hal fiyatlarıdır</b> (KDV ve rüsum durumu belediyeye göre değişir). Market, manav ve pazar fiyatları farklıdır.</li>
<li>Değişim oranı, aynı ürün ve çeşidin bir önceki bültendeki ortalama fiyatına göre hesaplanır.</li>
<li>Farklı şehirlerde aynı ürün farklı adlarla geçebilir; ürünler ada göre eşleştirilir ve hata olabilir.</li>
<li>Bilgiler bilgilendirme amaçlıdır; ticari kararlar için belediyenin resmi bültenini kontrol edin.</li>
</ul>
<p>Hata veya eksik bir şehir mi gördünüz? <a href="mailto:info@agilerelease.co.uk">info@agilerelease.co.uk</a></p>"""
    return page(site, "/hakkinda/", "Kaynaklar ve Açıklama – sebzehali.com",
                "sebzehali.com hal fiyatlarının kaynakları ve fiyatların nasıl hesaplandığı.", body)


def not_found(site):
    body = '<h1>Sayfa bulunamadı</h1><p><a href="/">Bugünkü hal fiyatlarına dön</a></p>'
    return page(site, "/404.html", "Sayfa bulunamadı – sebzehali.com", "Sayfa bulunamadı.", body)


# ---------------------------------------------------------------- main

def build(out, base_url):
    site = Site(load(), base_url)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    pages = {"/": home(site), "/hakkinda/": about_page(site)}
    for c in site.cities:
        pages[f"/hal/{c}/"] = city_page(site, c)
    for p in site.products:
        pages[f"/urun/{p}/"] = product_page(site, p)
    for path, content in pages.items():
        target = out / path.strip("/") / "index.html" if path != "/" else out / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (out / "404.html").write_text(not_found(site), encoding="utf-8")
    for f in STATIC.iterdir():
        shutil.copy(f, out / f.name)
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site.base}/sitemap.xml\n", encoding="utf-8")
    urls = "".join(f"<url><loc>{site.base}{p}</loc><lastmod>{site.newest}</lastmod></url>" for p in pages)
    (out / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8")
    host = base_url.split("//", 1)[-1].rstrip("/")
    (out / "CNAME").write_text(host + "\n", encoding="utf-8")
    return len(pages)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    ap.add_argument("--base-url", default="https://www.sebzehali.com")
    a = ap.parse_args(argv)
    n = build(pathlib.Path(a.out), a.base_url)
    print(f"built {n} pages into {a.out}")


if __name__ == "__main__":
    main()
