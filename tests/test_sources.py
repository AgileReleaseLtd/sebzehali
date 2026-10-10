"""Parse saved copies of each city's page, so a layout change shows up as a failing test."""

import pathlib
import unittest
from unittest import mock

from sebzehali.sources import bursa, izmir, konya

FIX = pathlib.Path(__file__).parent / "fixtures"


def serve(name):
    body = (FIX / name).read_text(encoding="utf-8")
    return mock.patch(f"sebzehali.sources.{name.split('.')[0]}.get", return_value=body)


class Sources(unittest.TestCase):
    def test_izmir(self):
        with serve("izmir.json"):
            date, rows = izmir.fetch("2026-10-09")
        self.assertEqual(date, "2026-10-09")
        self.assertGreater(len(rows), 50)
        self.assertEqual({r[5] for r in rows}, {"sebze", "meyve", "ithal"})

    def test_bursa(self):
        with serve("bursa.html"):
            date, rows = bursa.fetch("2026-10-10")
        self.assertEqual(date, "2026-10-09")
        cats = {r[5] for r in rows}
        self.assertTrue({"sebze", "meyve", "balik"} <= cats)
        tomato = [r for r in rows if r[0] == "Domates"][0]
        self.assertEqual((tomato[2], tomato[3]), ("10,00", "50,00"))

    def test_konya(self):
        with serve("konya.html"):
            date, rows = konya.fetch("2026-10-10")
        self.assertEqual(date, "2026-10-08")
        self.assertEqual({r[5] for r in rows}, {"sebze", "meyve"})
        self.assertGreater(len(rows), 100)


if __name__ == "__main__":
    unittest.main()
