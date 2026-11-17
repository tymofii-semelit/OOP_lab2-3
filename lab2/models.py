from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    price: Decimal


@dataclass(frozen=True)
class Barebone(Product):
    layout: str
    key_count: int
    stem: str
    description: str


@dataclass(frozen=True)
class SwitchPack(Product):
    quantity: int
    stem: str
    feel: str


@dataclass(frozen=True)
class KeycapSet(Product):
    quantity: int
    stem: str
    material: str
    layouts: tuple[str, ...]


@dataclass(frozen=True)
class Accessory(Product):
    pass


@dataclass(frozen=True)
class Promotion:
    id: str
    name: str
    kind: str
    value: Decimal
    minimum: Decimal


@dataclass(frozen=True)
class Keyboard:
    base: Barebone
    switches: SwitchPack
    keycaps: KeycapSet
    accessories: tuple[Accessory, ...]

    @property
    def price(self) -> Decimal:
        return sum(
            (item.price for item in (
                self.base, self.switches, self.keycaps, *self.accessories
            )),
            Decimal("0"),
        )


@dataclass(frozen=True)
class Quote:
    keyboard: Keyboard
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    promotion_name: str | None
