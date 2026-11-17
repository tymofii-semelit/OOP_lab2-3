from collections.abc import Callable
from decimal import Decimal

from .models import Product, Quote
from .shop import KeyboardShop


class ShopCLI:
    def __init__(
        self,
        shop: KeyboardShop,
        reader: Callable[[str], str] = input,
        writer: Callable[[str], None] = print,
    ):
        self.shop = shop
        self.read = reader
        self.write = writer
        self.last_quote: Quote | None = None

    @staticmethod
    def _money(value: Decimal) -> str:
        return f"{value:.2f} грн"

    @staticmethod
    def _parse_index(answer: str, count: int) -> int | None:
        if answer == "0":
            return 0
        if answer.isdigit():
            index = int(answer)
            if 1 <= index <= count:
                return index
        return None

    def run(self) -> None:
        while True:
            self.write("\n=== lab2 ===")
            self.write("1. Каталог товарів")
            self.write("2. Зібрати клавіатуру (Wizard)")
            self.write("3. Акції")
            self.write("4. Остання конфігурація")
            self.write("0. Вихід")
            action = self.read("Оберіть пункт: ").strip()
            if action == "0":
                self.write("До зустрічі!")
                return
            if action == "1":
                self.show_catalog()
            elif action == "2":
                self.wizard()
            elif action == "3":
                self.show_promotions()
            elif action == "4":
                if self.last_quote is None:
                    self.write("Ви ще не конфігурували клавіатуру.")
                else:
                    self.show_quote(self.last_quote)
            else:
                self.write("Такого пункту немає.")

    def show_catalog(self) -> None:
        catalog = self.shop.catalog
        quantities = {item.quantity for item in catalog.switches}
        switches_title = (
            f"Перемикачі (набір із {next(iter(quantities))} шт.)"
            if len(quantities) == 1
            else "Перемикачі"
        )
        for title, products in (
            ("Основи (Barebones)", catalog.barebones),
            (switches_title, catalog.switches),
            ("Кейкапи", catalog.keycaps),
            ("Аксесуари", catalog.accessories),
        ):
            self.write(f"\n--- {title} ---")
            for product in products:
                self.write(f"{product.name} — {self._money(product.price)}")

    def show_promotions(self) -> None:
        self.write("\n--- Акції ---")
        for promo in self.shop.catalog.promotions:
            self.write(f"{promo.name} (від {self._money(promo.minimum)})")

    def _choose(self, title: str, products: tuple[Product, ...]) -> Product | None:
        while True:
            self.write(f"\n{title}")
            for index, product in enumerate(products, 1):
                self.write(f"{index}. {product.name} — {self._money(product.price)}")
            self.write("0. Скасувати")
            answer = self.read("Номер: ").strip()
            index = self._parse_index(answer, len(products))
            if index == 0:
                return None
            if index is not None:
                return products[index - 1]
            self.write("Введіть номер із переліку.")

    def _select_accessories(self, base_id: str) -> tuple[str, ...]:
        recommended = self.shop.recommend(base_id)
        self.write("\nРекомендовані аксесуари:")
        if recommended:
            for item in recommended:
                self.write(f"- {item.name}")
        else:
            self.write("Немає рекомендацій.")

        accessories = self.shop.catalog.accessories
        chosen: list[str] = []
        while True:
            self.write("\nАксесуари (0 — завершити):")
            for index, item in enumerate(accessories, 1):
                mark = " [додано]" if item.id in chosen else ""
                self.write(f"{index}. {item.name} — {self._money(item.price)}{mark}")
            answer = self.read("Номер: ").strip()
            index = self._parse_index(answer, len(accessories))
            if index == 0:
                return tuple(chosen)
            if index is not None:
                item = accessories[index - 1]
                if item.id in chosen:
                    self.write("Цей аксесуар уже доданий.")
                else:
                    chosen.append(item.id)
            else:
                self.write("Введіть номер із переліку.")

    def _choose_promotion(self, subtotal: Decimal) -> str | None:
        available = tuple(
            promo for promo in self.shop.catalog.promotions if subtotal >= promo.minimum
        )
        self.write("\nДоступні акції:")
        if not available:
            self.write("Для цього замовлення немає доступних акцій.")
            return None
        for index, promo in enumerate(available, 1):
            self.write(f"{index}. {promo.name}")
        self.write("0. Без знижки")
        while True:
            answer = self.read("Номер акції: ").strip()
            index = self._parse_index(answer, len(available))
            if index == 0:
                return None
            if index is not None:
                return available[index - 1].id
            self.write("Введіть номер із переліку.")

    def wizard(self) -> None:
        catalog = self.shop.catalog
        base = self._choose("Крок 1/4. Оберіть основу", catalog.barebones)
        if base is None:
            return
        switches = self._choose("Крок 2/4. Оберіть перемикачі", catalog.switches)
        if switches is None:
            return
        keycaps = self._choose("Крок 3/4. Оберіть кейкапи", catalog.keycaps)
        if keycaps is None:
            return
        self.write("\nКрок 4/4. Оберіть необов'язкові аксесуари")
        accessories = self._select_accessories(base.id)
        try:
            keyboard = self.shop.configure(
                base.id, switches.id, keycaps.id, accessories
            )
            promo_id = self._choose_promotion(keyboard.price)
            self.last_quote = self.shop.quote(keyboard, promo_id)
            self.show_quote(self.last_quote)
        except (KeyError, ValueError) as error:
            self.write(f"Не вдалося скласти клавіатуру: {error}")

    def show_quote(self, quote: Quote) -> None:
        keyboard = quote.keyboard
        self.write("\n=== ВАША КЛАВІАТУРА ===")
        for item in (
            keyboard.base,
            keyboard.switches,
            keyboard.keycaps,
            *keyboard.accessories,
        ):
            self.write(f"{item.name}: {self._money(item.price)}")
        self.write(f"Сума: {self._money(quote.subtotal)}")
        if quote.promotion_name:
            self.write(f"Акція: {quote.promotion_name}")
        self.write(f"Знижка: {self._money(quote.discount)}")
        self.write(f"Разом: {self._money(quote.total)}")
