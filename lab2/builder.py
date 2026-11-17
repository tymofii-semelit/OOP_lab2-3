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

    def _required_parts(self) -> tuple[Barebone, SwitchPack, KeycapSet]:
        if self._base is None or self._switches is None or self._keycaps is None:
            raise ValueError("Вибери основу, перемикачі та кейкапи")
        return self._base, self._switches, self._keycaps

    @staticmethod
    def _validate_parts(
        base: Barebone, switches: SwitchPack, keycaps: KeycapSet
    ) -> None:
        if switches.quantity < base.key_count:
            raise ValueError("Не вистачає перемикачів для обраної основи")
        if keycaps.quantity < base.key_count:
            raise ValueError("Не вистачає кейкапів для обраної основи")
        if base.stem != switches.stem or base.stem != keycaps.stem:
            raise ValueError("Несумісний тип кріплення")
        if base.layout not in keycaps.layouts:
            raise ValueError("Набір кейкапів не підходить для цієї розкладки")

    def build(self) -> Keyboard:
        base, switches, keycaps = self._required_parts()
        self._validate_parts(base, switches, keycaps)
        return Keyboard(
            base=base,
            switches=switches,
            keycaps=keycaps,
            accessories=tuple(self._accessories.values()),
        )
