import json
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from lab2.catalog import CatalogError, JsonCatalogRepository
from lab2.factories import (
    AccessoryFactory,
    BareboneFactory,
    KeycapSetFactory,
    SwitchPackFactory,
)
from lab2.models import Accessory, Barebone, KeycapSet, SwitchPack


DATA = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = JsonCatalogRepository(DATA).load()

    def test_catalog_contents(self):
        self.assertEqual(len(self.catalog.barebones), 3)
        self.assertEqual(len(self.catalog.switches), 3)
        self.assertEqual(len(self.catalog.keycaps), 3)
        self.assertEqual(len(self.catalog.accessories), 3)
        self.assertEqual(len(self.catalog.promotions), 2)
        self.assertEqual(self.catalog.get_base("bb60").key_count, 61)
        self.assertEqual(self.catalog.get_switches("sw_linear").quantity, 90)
        self.assertEqual(self.catalog.get_keycaps("kc_pbt").material, "PBT")
        self.assertEqual(self.catalog.get_accessory("puller").price, Decimal("120"))
        self.assertEqual(self.catalog.get_promotion("welcome10").kind, "percent")

    def test_missing_product(self):
        for getter in (
            self.catalog.get_base,
            self.catalog.get_switches,
            self.catalog.get_keycaps,
            self.catalog.get_accessory,
            self.catalog.get_promotion,
        ):
            with self.subTest(getter=getter):
                with self.assertRaises(KeyError):
                    getter("missing")

    def test_factories_create_different_types(self):
        for factory, expected, group in (
            (BareboneFactory(), Barebone, "barebones"),
            (SwitchPackFactory(), SwitchPack, "switches"),
            (KeycapSetFactory(), KeycapSet, "keycaps"),
            (AccessoryFactory(), Accessory, "accessories"),
        ):
            with self.subTest(group=group):
                raw = json.loads(DATA.read_text(encoding="utf-8"))[group][0]
                result = factory.create(raw)
                self.assertIsInstance(result, expected)
                self.assertGreater(result.price, 0)

    def test_no_negative_price(self):
        with self.assertRaises(ValueError):
            AccessoryFactory().create({"id": "x", "name": "X", "price": "-1"})

    def load_modified(self, change):
        raw = json.loads(DATA.read_text(encoding="utf-8"))
        change(raw)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            return JsonCatalogRepository(path).load()

    def test_bad_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("{ nope", encoding="utf-8")
            with self.assertRaises(CatalogError):
                JsonCatalogRepository(path).load()

    def test_missing_catalog(self):
        with self.assertRaises(CatalogError):
            JsonCatalogRepository("missing-catalog-123.json").load()

    def test_invalid_catalog_data(self):
        changes = [
            lambda raw: raw["barebones"][0].update({"price": "-1"}),
            lambda raw: raw["barebones"][0].update({"key_count": 0}),
            lambda raw: raw["switches"][0].update({"quantity": 0}),
            lambda raw: raw["keycaps"][0].update({"quantity": 0}),
            lambda raw: raw["promotions"][0].update({"type": "unknown"}),
            lambda raw: raw["promotions"][0].update({"value": -1}),
            lambda raw: raw["promotions"][0].update({"minimum": -1}),
            lambda raw: raw["promotions"][0].update({"value": 120}),
            lambda raw: raw["recommendations"].update({"bad": ["puller"]}),
            lambda raw: raw["recommendations"]["bb60"].append("unknown"),
            lambda raw: raw["barebones"].append(raw["barebones"][0].copy()),
            lambda raw: raw["promotions"].append(raw["promotions"][0].copy()),
            lambda raw: raw.pop("keycaps"),
        ]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(CatalogError):
                    self.load_modified(change)

    def test_immutable_model(self):
        with self.assertRaises(AttributeError):
            self.catalog.get_base("bb60").price = Decimal("0")

    def test_replacing_model_for_test_fixtures(self):
        base = replace(self.catalog.get_base("bb60"), key_count=62)
        self.assertEqual(base.key_count, 62)
