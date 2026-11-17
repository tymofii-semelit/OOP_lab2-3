from .builder import KeyboardBuilder
from .catalog import Catalog
from .discounts import strategy_for
from .models import Accessory, Keyboard, Quote


class KeyboardShop:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def configure(
        self,
        base_id: str,
        switches_id: str,
        keycaps_id: str,
        accessory_ids: tuple[str, ...] = (),
    ) -> Keyboard:
        builder = (
            KeyboardBuilder()
            .set_base(self.catalog.get_base(base_id))
            .set_switches(self.catalog.get_switches(switches_id))
            .set_keycaps(self.catalog.get_keycaps(keycaps_id))
        )
        for accessory_id in accessory_ids:
            builder.add_accessory(self.catalog.get_accessory(accessory_id))
        return builder.build()

    def recommend(
        self, base_id: str, selected_ids: tuple[str, ...] = ()
    ) -> tuple[Accessory, ...]:
        self.catalog.get_base(base_id)
        ids = self.catalog.recommendations.get(base_id, ())
        return tuple(
            self.catalog.get_accessory(item_id)
            for item_id in ids
            if item_id not in selected_ids
        )

    def quote(self, keyboard: Keyboard, promotion_id: str | None = None) -> Quote:
        promotion = (
            self.catalog.get_promotion(promotion_id) if promotion_id else None
        )
        subtotal = keyboard.price
        discount = strategy_for(promotion).calculate(subtotal)
        return Quote(
            keyboard=keyboard,
            subtotal=subtotal,
            discount=discount,
            total=subtotal - discount,
            promotion_name=promotion.name if promotion else None,
        )
