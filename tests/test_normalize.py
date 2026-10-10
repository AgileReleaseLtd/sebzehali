import unittest

from sebzehali import normalize as n


class SplitName(unittest.TestCase):
    def check(self, raw, product, variety):
        self.assertEqual(n.split_name(raw), (product, variety), raw)

    def test_same_product_across_cities(self):
        self.check("BİBER  SİVRİ", "biber", "Sivri")      # İzmir
        self.check("Biber Sivri", "biber", "Sivri")       # Bursa
        self.check("BİBER (SİVRİ)", "biber", "Sivri")     # Konya

    def test_missing_turkish_letters_and_misspellings(self):
        self.check("CILEK", "cilek", "")
        self.check("AVAKADO", "avokado", "")
        self.check("MAYDONOZ (MUHTELİF)", "maydanoz", "")
        self.check("Karnıbahar", "karnabahar", "")

    def test_qualifier_before_product(self):
        self.check("Kuru Soğan", "sogan", "Kuru")
        self.check("SOĞAN (KURU)", "sogan", "Kuru")

    def test_two_word_products(self):
        self.check("DENIZ BÖRÜLCESİ", "deniz-borulcesi", "")
        self.check("Bal Kabağı", "bal-kabagi", "")

    def test_izmir_fresh_herb_prefix(self):
        self.check("Y.DEREOTU", "dereotu", "")


class Prices(unittest.TestCase):
    def test_parse_price(self):
        self.assertEqual(n.parse_price("1.250,50 ₺"), 1250.5)
        self.assertEqual(n.parse_price("35"), 35.0)
        self.assertEqual(n.parse_price(40), 40.0)
        self.assertIsNone(n.parse_price("-"))

    def test_row_swaps_reversed_range_and_fills_missing_side(self):
        r = n.normalize_row("Domates", "Kg.", "80", "35", None, "sebze")
        self.assertEqual((r["min"], r["max"], r["unit"]), (35.0, 80.0, "kg"))
        r = n.normalize_row("Domates", "Kg", None, "50", None, "sebze")
        self.assertEqual((r["min"], r["max"]), (50.0, 50.0))
        self.assertIsNone(n.normalize_row("Domates", "Kg", None, None, None, "sebze"))

    def test_units(self):
        self.assertEqual(n.normalize_unit("(Adet)"), "adet")
        self.assertEqual(n.normalize_unit("Demet"), "bağ")
        self.assertEqual(n.normalize_unit("BAĞ"), "bağ")


class TurkishCase(unittest.TestCase):
    def test_dotted_i(self):
        self.assertEqual(n.tr_lower("İNCİR"), "incir")
        self.assertEqual(n.tr_lower("ISPANAK"), "ıspanak")
        self.assertEqual(n.slugify("Çilek Şeftali Üzüm"), "cilek-seftali-uzum")


if __name__ == "__main__":
    unittest.main()
