import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from lab2.builder import KeyboardBuilder
from lab2.catalog import JsonCatalogRepository
from lab2.shop import KeyboardShop


DATA = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = JsonCatalogRepository(DATA).load()
        cls.shop = KeyboardShop(cls.catalog)

    def build(self, base=None, switches=None, keycaps=None):
        return (
            KeyboardBuilder()
            .set_base(base or self.catalog.get_base("bb60"))
            .set_switches(switches or self.catalog.get_switches("sw_linear"))
            .set_keycaps(keycaps or self.catalog.get_keycaps("kc_abs"))
            .build()
        )

    def test_complete_configuration(self):
        keyboard = self.shop.configure(
            "bb75", "sw_tactile", "kc_pbt", ("puller", "cable")
        )
        self.assertEqual(keyboard.base.layout, "75%")
        self.assertEqual(len(keyboard.accessories), 2)
        self.assertEqual(keyboard.price, Decimal("3680"))

    def test_omitted_configuration(self):
        with self.assertRaisesRegex(ValueError, "Вибери основу"):
            KeyboardBuilder().build()

    def test_insufficient_switches(self):
        switches = replace(self.catalog.get_switches("sw_linear"), quantity=60)
        with self.assertRaisesRegex(ValueError, "перемикачів"):
            self.build(switches=switches)

    def test_insufficient_keycaps(self):
        keycaps = replace(self.catalog.get_keycaps("kc_abs"), quantity=60)
        with self.assertRaisesRegex(ValueError, "кейкапів"):
            self.build(keycaps=keycaps)

    def test_incompatible_stem(self):
        switches = replace(self.catalog.get_switches("sw_linear"), stem="other")
        with self.assertRaisesRegex(ValueError, "кріплення"):
            self.build(switches=switches)
        caps = replace(self.catalog.get_keycaps("kc_abs"), stem="other")
        with self.assertRaisesRegex(ValueError, "кріплення"):
            self.build(keycaps=caps)

    def test_incompatible_layout(self):
        caps = replace(self.catalog.get_keycaps("kc_abs"), layouts=("TKL",))
        with self.assertRaisesRegex(ValueError, "розкладки"):
            self.build(keycaps=caps)

    def test_duplicate_accessory_is_counted_once(self):
        keyboard = self.shop.configure(
            "bb60", "sw_linear", "kc_abs", ("puller", "puller")
        )
        self.assertEqual(len(keyboard.accessories), 1)
        self.assertEqual(keyboard.price, Decimal("2530"))

    def test_recommendations(self):
        items = self.shop.recommend("bb60")
        self.assertEqual([item.id for item in items], ["puller", "cable"])
        items = self.shop.recommend("bb60", ("puller",))
        self.assertEqual([item.id for item in items], ["cable"])
        self.assertEqual(self.shop.recommend("bb60", ("puller", "cable")), ())
        with self.assertRaises(KeyError):
            self.shop.recommend("missing")

    def test_invalid_ids(self):
        with self.assertRaises(KeyError):
            self.shop.configure("missing", "sw_linear", "kc_abs")
        with self.assertRaises(KeyError):
            self.shop.configure("bb60", "missing", "kc_abs")
        with self.assertRaises(KeyError):
            self.shop.configure("bb60", "sw_linear", "missing")
        with self.assertRaises(KeyError):
            self.shop.configure("bb60", "sw_linear", "kc_abs", ("missing",))
