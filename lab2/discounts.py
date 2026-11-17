from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP

from .models import Promotion


class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, subtotal: Decimal) -> Decimal:
        pass


class NoDiscount(DiscountStrategy):
    def calculate(self, subtotal: Decimal) -> Decimal:
        return Decimal("0.00")


class PercentageDiscount(DiscountStrategy):
    def __init__(self, percent: Decimal, minimum: Decimal):
        self.percent = percent
        self.minimum = minimum

    def calculate(self, subtotal: Decimal) -> Decimal:
        if subtotal < self.minimum:
            return Decimal("0.00")
        return (subtotal * self.percent / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


class FixedDiscount(DiscountStrategy):
    def __init__(self, amount: Decimal, minimum: Decimal):
        self.amount = amount
        self.minimum = minimum

    def calculate(self, subtotal: Decimal) -> Decimal:
        if subtotal < self.minimum:
            return Decimal("0.00")
        return min(self.amount, subtotal)


def strategy_for(promotion: Promotion | None) -> DiscountStrategy:
    if promotion is None:
        return NoDiscount()
    if promotion.kind == "percent":
        return PercentageDiscount(promotion.value, promotion.minimum)
    if promotion.kind == "fixed":
        return FixedDiscount(promotion.value, promotion.minimum)
    raise ValueError(f"Невідома стратегія знижки: {promotion.kind}")
