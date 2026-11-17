import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .factories import (
    AccessoryFactory,
    BareboneFactory,
    KeycapSetFactory,
    SwitchPackFactory,
)
from .models import Accessory, Barebone, KeycapSet, Promotion, SwitchPack


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class Catalog:
    barebones: tuple[Barebone, ...]
    switches: tuple[SwitchPack, ...]
    keycaps: tuple[KeycapSet, ...]
    accessories: tuple[Accessory, ...]
    promotions: tuple[Promotion, ...]
    recommendations: dict[str, tuple[str, ...]]

    @staticmethod
    def _get(items: tuple, product_id: str):
        for item in items:
            if item.id == product_id:
                return item
        raise KeyError(f"Невідомий ідентифікатор: {product_id}")

    def get_base(self, product_id: str) -> Barebone:
        return self._get(self.barebones, product_id)

    def get_switches(self, product_id: str) -> SwitchPack:
        return self._get(self.switches, product_id)

    def get_keycaps(self, product_id: str) -> KeycapSet:
        return self._get(self.keycaps, product_id)

    def get_accessory(self, product_id: str) -> Accessory:
        return self._get(self.accessories, product_id)

    def get_promotion(self, promotion_id: str) -> Promotion:
        return self._get(self.promotions, promotion_id)


class JsonCatalogRepository:
    FACTORIES = {
        "barebones": BareboneFactory(),
        "switches": SwitchPackFactory(),
        "keycaps": KeycapSetFactory(),
        "accessories": AccessoryFactory(),
    }

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> Catalog:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            groups = self._load_products(raw)
            promotions = self._load_promotions(raw)
            recommendations = self._load_recommendations(raw)
            catalog = Catalog(
                **groups,
                promotions=promotions,
                recommendations=recommendations,
            )
            self._validate(catalog)
            return catalog
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            InvalidOperation,
        ) as error:
            if isinstance(error, CatalogError):
                raise
            raise CatalogError(f"Помилка завантаження каталогу: {error}") from error

    @staticmethod
    def _check_unique_ids(items: tuple, message: str) -> None:
        identifiers = [item.id for item in items]
        if len(set(identifiers)) != len(identifiers):
            raise CatalogError(message)

    def _load_products(self, raw: dict) -> dict:
        groups = {
            name: tuple(factory.create(item) for item in raw[name])
            for name, factory in self.FACTORIES.items()
        }
        for name, items in groups.items():
            self._check_unique_ids(items, f"Повторюються ID в розділі {name}")
        return groups

    def _load_promotions(self, raw: dict) -> tuple[Promotion, ...]:
        promotions = tuple(
            Promotion(
                id=str(item["id"]),
                name=str(item["name"]),
                kind=str(item["type"]),
                value=Decimal(str(item["value"])),
                minimum=Decimal(str(item["minimum"])),
            )
            for item in raw["promotions"]
        )
        self._check_unique_ids(promotions, "Повторюються ID акцій")
        return promotions

    @staticmethod
    def _load_recommendations(raw: dict) -> dict[str, tuple[str, ...]]:
        return {
            str(base_id): tuple(ids) for base_id, ids in raw["recommendations"].items()
        }

    @staticmethod
    def _validate(catalog: Catalog) -> None:
        for base in catalog.barebones:
            if base.key_count <= 0:
                raise CatalogError("Кількість клавіш має бути додатною")
        for item in (*catalog.switches, *catalog.keycaps):
            if item.quantity <= 0:
                raise CatalogError("Кількість деталей має бути додатною")
        for promotion in catalog.promotions:
            if promotion.kind not in {"percent", "fixed"}:
                raise CatalogError("Невідомий тип акції")
            if promotion.value < 0 or promotion.minimum < 0:
                raise CatalogError("Параметри акції не можуть бути від'ємними")
            if promotion.kind == "percent" and promotion.value > 100:
                raise CatalogError("Знижка не може перевищувати 100%")
        for base_id, accessory_ids in catalog.recommendations.items():
            catalog.get_base(base_id)
            for accessory_id in accessory_ids:
                catalog.get_accessory(accessory_id)
