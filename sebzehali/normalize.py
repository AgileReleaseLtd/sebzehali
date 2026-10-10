"""Turn each city's raw product rows into one shared shape.

Every source returns rows like ("DOMATES (SALKIM)", "Kg", 35, 80, None, "sebze"). Cities spell
the same product differently ("BİBER  SİVRİ", "Biber Sivri", "BİBER (SİVRİ)", "CILEK" for
"ÇİLEK"), so products are matched on an ASCII slug of the first word, and the rest of the
name becomes the variety.
"""

import re

_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")

# Words that come before the product name ("Kuru soğan", "Taze fasulye").
_LEADING_QUALIFIERS = {"kuru", "taze", "yesil", "kirmizi", "beyaz", "siyah", "sari", "ithal", "yerli"}

# Products whose name is two words; matched before the first-word rule.
_TWO_WORD_PRODUCTS = {
    "deniz borulcesi": "deniz-borulcesi",
    "dere otu": "dereotu",
    "hindistan cevizi": "hindistan-cevizi",
    "kara lahana": "kara-lahana",
    "frenk sogani": "frenk-sogani",
    "taze sogan": "taze-sogan",
    "yer elmasi": "yer-elmasi",
    "kuzu kulagi": "kuzukulagi",
    "deniz otu": "deniz-borulcesi",
    "semiz otu": "semizotu",
    "eksi ot": "eksi-ot",
    "altin cilek": "altin-cilek",
    "ejder meyvesi": "ejder-meyvesi",
    "yaban mersini": "yaban-mersini",
    "bal kabagi": "bal-kabagi",
    "kara dut": "dut",
    "ciplak mezgit": "mezgit",
    "norvec somonu": "somon",
    "bruksel lahanasi": "bruksel-lahanasi",
    "tatli patates": "tatli-patates",
    "trabzon hurmasi": "trabzon-hurmasi",
    "yeni dunya": "yeni-dunya",
}

# Misspellings and alternative names seen in the bulletins, keyed by slug.
_ALIASES = {
    "avakado": "avokado",
    "fasulye": "fasulye",
    "fasulya": "fasulye",
    "borulce": "borulce",
    "bogrulce": "borulce",
    "brokoli": "brokoli",
    "karpuz": "karpuz",
    "mandalin": "mandalina",
    "kivi": "kivi",
    "nane": "nane",
    "patlican": "patlican",
    "salatalik": "salatalik",
    "hiyar": "salatalik",
    "kayisi": "kayisi",
    "mantar": "mantar",
    "sarmisak": "sarimsak",
    "sarimsak": "sarimsak",
    "darı": "misir",
    "dari": "misir",
    "misir": "misir",
    "maydonoz": "maydanoz",
    "karnibahar": "karnabahar",
    "semiz": "semizotu",
    "bluberry": "yaban-mersini",
    "blueberry": "yaban-mersini",
    "bas": "sarimsak",
    "balkabagi": "bal-kabagi",
    "dolmalik": "biber",
    "karadenizyapragi": "karadeniz-yapragi",
    "altincilek": "altin-cilek",
    "karalahana": "kara-lahana",
    "mersin": "yaban-mersini",
    "rozmerin": "biberiye",
}

# Display names for products whose bulletin spelling is often all-caps or lacks Turkish letters.
PRODUCT_NAMES = {
    "acur": "Acur", "ahududu": "Ahududu", "ananas": "Ananas", "armut": "Armut", "avokado": "Avokado",
    "ayva": "Ayva", "bamya": "Bamya", "barbunya": "Barbunya", "bezelye": "Bezelye", "biber": "Biber",
    "borulce": "Börülce", "brokoli": "Brokoli", "cilek": "Çilek", "deniz-borulcesi": "Deniz börülcesi",
    "dereotu": "Dereotu", "domates": "Domates", "elma": "Elma", "enginar": "Enginar", "erik": "Erik",
    "fasulye": "Fasulye", "greyfurt": "Greyfurt", "havuc": "Havuç", "hurma": "Hurma", "incir": "İncir",
    "ispanak": "Ispanak", "kabak": "Kabak", "karnabahar": "Karnabahar", "karpuz": "Karpuz",
    "kavun": "Kavun", "kayisi": "Kayısı", "kestane": "Kestane", "kiraz": "Kiraz", "kivi": "Kivi",
    "lahana": "Lahana", "limon": "Limon", "mandalina": "Mandalina", "mantar": "Mantar",
    "marul": "Marul", "maydanoz": "Maydanoz", "misir": "Mısır", "muz": "Muz", "nane": "Nane",
    "nar": "Nar", "patates": "Patates", "patlican": "Patlıcan", "pirasa": "Pırasa", "portakal": "Portakal",
    "roka": "Roka", "salatalik": "Salatalık", "sarimsak": "Sarımsak", "sogan": "Soğan",
    "seftali": "Şeftali", "taze-sogan": "Taze soğan", "turp": "Turp", "uzum": "Üzüm",
    "visne": "Vişne", "zencefil": "Zencefil", "kereviz": "Kereviz", "semizotu": "Semizotu",
    "hamsi": "Hamsi", "istavrit": "İstavrit", "levrek": "Levrek", "cipura": "Çipura",
    "somon": "Somon", "palamut": "Palamut", "sardalya": "Sardalya", "mezgit": "Mezgit",
    "alabalik": "Alabalık", "lufer": "Lüfer", "kalamar": "Kalamar", "karides": "Karides",
    "kuzukulagi": "Kuzukulağı", "eksi-ot": "Ekşi ot", "altin-cilek": "Altın çilek", "ejder-meyvesi": "Ejder meyvesi",
    "yaban-mersini": "Yaban mersini", "bal-kabagi": "Bal kabağı", "mezgit": "Mezgit", "hindistan-cevizi": "Hindistan cevizi",
    "yer-elmasi": "Yer elması", "bruksel-lahanasi": "Brüksel lahanası", "tatli-patates": "Tatlı patates",
    "trabzon-hurmasi": "Trabzon hurması", "yeni-dunya": "Yeni dünya", "kara-lahana": "Kara lahana",
    "karadeniz-yapragi": "Karadeniz yaprağı", "biberiye": "Biberiye", "kisnis": "Kişniş", "kuskonmaz": "Kuşkonmaz", "pazi": "Pazı", "tere": "Tere", "feslegen": "Fesleğen", "reyhan": "Reyhan",
    "pancar": "Pancar", "nektarin": "Nektarin", "mango": "Mango", "dut": "Dut", "salgam": "Şalgam",
    "bogurtlen": "Böğürtlen", "kizilcik": "Kızılcık", "hunnap": "Hünnap", "uskumru": "Uskumru",
    "cinekop": "Çinekop", "kefal": "Kefal", "alic": "Alıç", "kekik": "Kekik", "endivyen": "Endivyen",
}

_UNITS = {
    "kg": "kg", "kilo": "kg", "kilogram": "kg",
    "adet": "adet", "ad": "adet",
    "bag": "bağ", "demet": "bağ",
    "koli": "koli", "kasa": "kasa", "paket": "paket", "kutu": "kutu", "ton": "ton",
}

CATEGORIES = {"sebze": "Sebze", "meyve": "Meyve", "ithal": "İthal", "balik": "Balık ve deniz ürünleri"}


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_upper_first(s):
    if not s:
        return s
    first = {"i": "İ", "ı": "I"}.get(s[0], s[0].upper())
    return first + s[1:]


def slugify(s):
    s = tr_lower(s).translate(_ASCII)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def parse_price(s):
    """'1.250,50 ₺' -> 1250.5; '35' -> 35.0; '' or '-' -> None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = re.sub(r"[^\d.,]", "", str(s))
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def normalize_unit(s):
    key = slugify(s or "").replace("-", "")
    return _UNITS.get(key, key or "kg")


def split_name(raw):
    """'BİBER  SİVRİ (DİĞER)' -> ('biber', 'Sivri (diğer)')."""
    name = re.sub(r"^\s*Y\.\s*", "", raw)  # İzmir writes "Y.DEREOTU" for fresh (yeşil) herbs
    name = re.sub(r"\s+", " ", name.replace("(", " (").replace("-", " ").replace(".", ". ")).strip()
    words = name.split(" ")
    lowered = [slugify(w) for w in words]

    for n in (2,):
        key = " ".join(lowered[:n])
        if len(words) >= n and key in _TWO_WORD_PRODUCTS:
            return _TWO_WORD_PRODUCTS[key], _variety(words[n:])

    first = re.sub(r"[^a-z0-9]", "", lowered[0])
    rest = words[1:]
    if first in _LEADING_QUALIFIERS and len(words) > 1:
        second = re.sub(r"[^a-z0-9]", "", lowered[1])
        if second:
            first, rest = second, [words[0]] + words[2:]
    product = _ALIASES.get(first, first)
    return product, _variety(rest)


def _variety(words):
    text = " ".join(words).strip()
    text = re.sub(r"[()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .,-")
    if slugify(text) in ("muhtelif", "diger", ""):
        return ""  # "various" / "other": the generic row for the product
    return tr_upper_first(tr_lower(text)) if text else ""


def product_name(slug, raw_samples=()):
    if slug in PRODUCT_NAMES:
        return PRODUCT_NAMES[slug]
    for raw in raw_samples:
        return tr_upper_first(tr_lower(raw.split(" ")[0].strip("()")))
    return slug.replace("-", " ").capitalize()


def normalize_row(raw_name, unit, low, high, avg, category):
    product, variety = split_name(raw_name)
    if not product:
        return None
    low, high, avg = parse_price(low), parse_price(high), parse_price(avg)
    if low is None and high is None:
        return None
    if low is None:
        low = high
    if high is None:
        high = low
    if low > high:
        low, high = high, low
    return {
        "raw": raw_name.strip(),
        "product": product,
        "variety": variety,
        "unit": normalize_unit(unit),
        "min": round(low, 2),
        "max": round(high, 2),
        "avg": round(avg, 2) if avg else None,
        "category": category,
    }
