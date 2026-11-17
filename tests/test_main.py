import unittest
from unittest.mock import patch

import main
from lab2.catalog import CatalogError


class MainTests(unittest.TestCase):
    @patch("main.ShopCLI")
    @patch("main.KeyboardShop")
    @patch("main.JsonCatalogRepository")
    def test_main_starts_app(self, repository, shop, cli):
        main.main()
        repository.return_value.load.assert_called_once_with()
        shop.assert_called_once_with(repository.return_value.load.return_value)
        cli.return_value.run.assert_called_once_with()

    @patch("builtins.print")
    @patch("main.JsonCatalogRepository")
    def test_main_reports_catalog_error(self, repository, output):
        repository.return_value.load.side_effect = CatalogError("помилка читання")
        main.main()
        output.assert_called_once_with("Помилка: помилка читання")

    @patch("builtins.print")
    @patch("main.ShopCLI")
    def test_main_handles_keyboard_interrupt(self, cli, output):
        cli.return_value.run.side_effect = KeyboardInterrupt
        main.main()
        output.assert_called_once_with("\nПрограму завершено.")

    @patch("builtins.print")
    @patch("main.ShopCLI")
    def test_main_handles_eof(self, cli, output):
        cli.return_value.run.side_effect = EOFError
        main.main()
        output.assert_called_once_with("\nПрограму завершено.")
