from .models import Accessory, Barebone, Keyboard, KeycapSet, SwitchPack


class KeyboardBuilder:
    def __init__(self):
        self._base: Barebone | None = None
        self._switches: SwitchPack | None = None
        self._keycaps: KeycapSet | None = None
        self._accessories: dict[str, Accessory] = {}

    def set_base(self, base: Barebone) -> "KeyboardBuilder":
        self._base = base
        return self

    def set_switches(self, switches: SwitchPack) -> "KeyboardBuilder":
        self._switches = switches
        return self

    def set_keycaps(self, keycaps: KeycapSet) -> "KeyboardBuilder":
        self._keycaps = keycaps
        return self

    def add_accessory(self, accessory: Accessory) -> "KeyboardBuilder":
        self._accessories[accessory.id] = accessory
        return self

    def build(self) -> Keyboard:
        if self._base is None or self._switches is None or self._keycaps is None:
            raise ValueError("Вибери основу, перемикачі та кейкапи")
        if self._switches.quantity < self._base.key_count:
            raise ValueError("Не вистачає перемикачів для обраної основи")
        if self._keycaps.quantity < self._base.key_count:
            raise ValueError("Не вистачає кейкапів для обраної основи")
        if self._base.stem != self._switches.stem or self._base.stem != self._keycaps.stem:
            raise ValueError("Несумісний тип кріплення")
        if self._base.layout not in self._keycaps.layouts:
            raise ValueError("Набір кейкапів не підходить для цієї розкладки")
        return Keyboard(
            base=self._base,
            switches=self._switches,
            keycaps=self._keycaps,
            accessories=tuple(self._accessories.values()),
        )
