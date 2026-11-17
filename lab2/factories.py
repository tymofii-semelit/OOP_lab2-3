from abc import ABC, abstractmethod
from decimal import Decimal

from .models import Accessory, Barebone, KeycapSet, Product, SwitchPack


class ProductFactory(ABC):
    def create(self, raw: dict) -> Product:
        price = Decimal(str(raw["price"]))
        if price < 0:
            raise ValueError("Ціна товару не може бути від'ємною")
        common = {"id": str(raw["id"]), "name": str(raw["name"]), "price": price}
        return self._create_product(raw, common)

    @abstractmethod
    def _create_product(self, raw: dict, common: dict) -> Product:
        pass


class BareboneFactory(ProductFactory):
    def _create_product(self, raw: dict, common: dict) -> Barebone:
        return Barebone(
            **common,
            layout=str(raw["layout"]),
            key_count=int(raw["key_count"]),
            stem=str(raw["stem"]),
            description=str(raw["description"]),
        )


class SwitchPackFactory(ProductFactory):
    def _create_product(self, raw: dict, common: dict) -> SwitchPack:
        return SwitchPack(
            **common,
            quantity=int(raw["quantity"]),
            stem=str(raw["stem"]),
            feel=str(raw["feel"]),
        )


class KeycapSetFactory(ProductFactory):
    def _create_product(self, raw: dict, common: dict) -> KeycapSet:
        return KeycapSet(
            **common,
            quantity=int(raw["quantity"]),
            stem=str(raw["stem"]),
            material=str(raw["material"]),
            layouts=tuple(raw["layouts"]),
        )


class AccessoryFactory(ProductFactory):
    def _create_product(self, raw: dict, common: dict) -> Accessory:
        return Accessory(**common)
