import unittest
from decimal import Decimal
from pathlib import Path

from lab2.catalog import JsonCatalogRepository
from lab2.discounts import (
    FixedDiscount,
    NoDiscount,
    PercentageDiscount,
    strategy_for,
)
from lab2.models import Promotion
from lab2.shop import KeyboardShop


DATA = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


class DiscountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shop = KeyboardShop(JsonCatalogRepository(DATA).load())

    def test_no_discount(self):
        quote = self.shop.quote(
            self.shop.configure("bb60", "sw_linear", "kc_abs")
        )
        self.assertEqual(quote.subtotal, Decimal("2410"))
        self.assertEqual(quote.discount, 0)
        self.assertEqual(quote.total, quote.subtotal)
        self.assertIsNone(quote.promotion_name)
        self.assertEqual(NoDiscount().calculate(Decimal("100")), 0)

    def test_percent_discount_and_threshold(self):
        keyboard = self.shop.configure("bb75", "sw_linear", "kc_pbt")
        quote = self.shop.quote(keyboard, "welcome10")
        self.assertEqual(quote.subtotal, Decimal("3040"))
        self.assertEqual(quote.discount, Decimal("304"))
        self.assertEqual(quote.total, Decimal("2736"))
        self.assertIsNotNone(quote.promotion_name)
        low = self.shop.configure("bb60", "sw_linear", "kc_abs")
        self.assertEqual(self.shop.quote(low, "welcome10").discount, 0)

    def test_fixed_discount_and_threshold(self):
        keyboard = self.shop.configure("bbtkl", "sw_linear", "kc_pbt")
        quote = self.shop.quote(keyboard, "minus200")
        self.assertEqual(quote.subtotal, Decimal("3390"))
        self.assertEqual(quote.discount, Decimal("200"))
        self.assertEqual(quote.total, Decimal("3190"))
        low = self.shop.configure("bb60", "sw_linear", "kc_abs")
        self.assertEqual(self.shop.quote(low, "minus200").discount, 0)

    def test_percent_rounding(self):
        strategy = PercentageDiscount(Decimal("7"), Decimal("0"))
        self.assertEqual(strategy.calculate(Decimal("12.50")), Decimal("0.88"))

    def test_fixed_discount_cannot_exceed_price(self):
        strategy = FixedDiscount(Decimal("150"), Decimal("0"))
        self.assertEqual(strategy.calculate(Decimal("100")), Decimal("100"))

    def test_invalid_strategy(self):
        promo = Promotion("x", "Unknown", "mystery", Decimal("1"), Decimal("0"))
        with self.assertRaises(ValueError):
            strategy_for(promo)

    def test_missing_promotion(self):
        keyboard = self.shop.configure("bb60", "sw_linear", "kc_abs")
        with self.assertRaises(KeyError):
            self.shop.quote(keyboard, "missing")
