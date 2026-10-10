import pathlib
import tempfile
import unittest

from sebzehali import build


class Build(unittest.TestCase):
    def test_builds_from_stored_data(self):
        with tempfile.TemporaryDirectory() as d:
            n = build.build(pathlib.Path(d), "https://www.sebzehali.com")
            out = pathlib.Path(d)
            self.assertGreater(n, 20)
            home = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("Bugünkü hal fiyatları", home)
            self.assertIn('href="/urun/domates/"', home)
            self.assertIn("<svg", (out / "urun/domates/index.html").read_text(encoding="utf-8"))
            self.assertEqual((out / "CNAME").read_text().strip(), "www.sebzehali.com")
            self.assertIn("/hal/izmir/", (out / "sitemap.xml").read_text())


if __name__ == "__main__":
    unittest.main()
