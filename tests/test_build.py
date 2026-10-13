import pathlib
import tempfile
import unittest
from unittest import mock

from sebzehali import build, config


class Build(unittest.TestCase):
    def test_builds_from_stored_data(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(config, "GA_MEASUREMENT_ID", "G-TEST123"):
            n = build.build(pathlib.Path(d), "https://www.sebzehali.com")
            out = pathlib.Path(d)
            self.assertGreater(n, 20)
            home = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("Bugünkü hal fiyatları", home)
            self.assertIn('href="/urun/domates/"', home)
            self.assertIn("<svg", (out / "urun/domates/index.html").read_text(encoding="utf-8"))
            self.assertEqual((out / "CNAME").read_text().strip(), "www.sebzehali.com")
            self.assertIn("/hal/izmir/", (out / "sitemap.xml").read_text())
            self.assertTrue((out / "hal/izmir/domates/index.html").exists())
            self.assertTrue((out / "haftalik/index.html").exists())
            for p in ("gizlilik", "iletisim"):
                self.assertIn("info@agilerelease.co.uk", (out / p / "index.html").read_text(encoding="utf-8"))
            # Google Analytics only after consent: pages carry the hidden bar, never the Google tag itself.
            self.assertIn('data-ga="G-TEST123"', home)
            self.assertIn('id="cerez"', home)
            self.assertNotIn("googletagmanager", home)
            self.assertTrue((out / "cerez.js").exists())
            privacy = (out / "gizlilik/index.html").read_text(encoding="utf-8")
            self.assertIn("_ga_TEST123", privacy)
            self.assertIn('data-cerez="sor"', privacy)

    def test_no_analytics_without_ids(self):
        with mock.patch.object(config, "GA_MEASUREMENT_ID", ""), \
                mock.patch.object(config, "CLOUDFLARE_BEACON_TOKEN", ""):
            self.assertEqual(build.analytics_snippet(), "")


if __name__ == "__main__":
    unittest.main()
