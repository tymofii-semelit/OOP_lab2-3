import unittest
from dataclasses import replace
from pathlib import Path

from lab2.catalog import JsonCatalogRepository
from lab2.cli import ShopCLI
from lab2.shop import KeyboardShop


DATA = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = JsonCatalogRepository(DATA).load()

    def create_cli(self, responses, catalog=None):
        iterator = iter(responses)
        output = []
        cli = ShopCLI(
            KeyboardShop(catalog or self.catalog),
            reader=lambda message: next(iterator),
            writer=output.append,
        )
        return cli, output

    def test_catalog_and_promotions(self):
        cli, output = self.create_cli([])
        cli.show_catalog()
        cli.show_promotions()
        self.assertTrue(any("lab2 Compact" in line for line in output))
        self.assertTrue(any("Акції" in line for line in output))

    def test_run_menu_and_exit(self):
        cli, output = self.create_cli(["???", "4", "1", "3", "0"])
        cli.run()
        self.assertTrue(any("Такого пункту" in line for line in output))
        self.assertTrue(any("ще не" in line for line in output))
        self.assertTrue(any("До зустрічі" in line for line in output))

    def test_complete_wizard_from_menu(self):
        cli, output = self.create_cli([
            "2", "bad", "2", "1", "2", "bad", "1", "1", "1", "0", "1", "4", "0"
        ])
        cli.run()
        self.assertIsNotNone(cli.last_quote)
        self.assertEqual(cli.last_quote.keyboard.base.id, "bb75")
        self.assertEqual(len(cli.last_quote.keyboard.accessories), 1)
        self.assertGreater(cli.last_quote.discount, 0)
        self.assertTrue(any("[додано]" in line for line in output))
        self.assertTrue(any("уже доданий" in line for line in output))
        self.assertTrue(any("Разом:" in line for line in output))

    def test_wizard_cancel_each_step(self):
        for responses in (["0"], ["1", "0"], ["1", "1", "0"]):
            with self.subTest(responses=responses):
                cli, _ = self.create_cli(responses)
                cli.wizard()
                self.assertIsNone(cli.last_quote)

    def test_wizard_without_accessories_and_promotion(self):
        cli, output = self.create_cli(["1", "1", "1", "0"])
        cli.wizard()
        self.assertIsNotNone(cli.last_quote)
        self.assertEqual(cli.last_quote.discount, 0)
        self.assertTrue(any("немає доступних" in line for line in output))

    def test_wizard_promotion_skip_and_retry(self):
        cli, output = self.create_cli(["2", "2", "2", "0", "oops", "0"])
        cli.wizard()
        self.assertEqual(cli.last_quote.discount, 0)
        self.assertTrue(any("Введіть номер" in line for line in output))

    def test_recommendations_and_invalid_accessory_selection(self):
        cli, output = self.create_cli(["oops", "99", "1", "1", "0"])
        selected = cli._select_accessories("bb60")
        self.assertEqual(selected, ("puller",))
        self.assertTrue(any("Введіть номер" in line for line in output))
        self.assertTrue(any("уже доданий" in line for line in output))

    def test_wizard_reports_incompatibility(self):
        bad_switch = replace(self.catalog.switches[0], quantity=1)
        catalog = replace(
            self.catalog,
            switches=(bad_switch, *self.catalog.switches[1:]),
        )
        cli, output = self.create_cli(["1", "1", "1", "0"], catalog)
        cli.wizard()
        self.assertIsNone(cli.last_quote)
        self.assertTrue(any("Не вдалося" in line for line in output))

    def test_no_recommendations(self):
        catalog = replace(self.catalog, recommendations={})
        cli, output = self.create_cli(["0"], catalog)
        self.assertEqual(cli._select_accessories("bb60"), ())
        self.assertTrue(any("Немає рекомендацій" in line for line in output))

    def test_product_selection_handles_invalid_numbers(self):
        cli, output = self.create_cli(["-2", "2.5", "000", "99", "1"])
        product = cli._choose("Оберіть основу", self.catalog.barebones)
        self.assertEqual(product.id, "bb60")
        self.assertEqual(sum("Введіть номер" in line for line in output), 4)

    def test_switch_quantity_is_not_hardcoded(self):
        updated = tuple(replace(item, quantity=120) for item in self.catalog.switches)
        catalog = replace(self.catalog, switches=updated)
        cli, output = self.create_cli([], catalog)
        cli.show_catalog()
        self.assertTrue(any("набір із 120 шт." in line for line in output))

    def test_catalog_with_different_switch_pack_sizes(self):
        first = replace(self.catalog.switches[0], quantity=80)
        catalog = replace(self.catalog, switches=(first, *self.catalog.switches[1:]))
        cli, output = self.create_cli([], catalog)
        cli.show_catalog()
        self.assertIn("\n--- Перемикачі ---", output)
