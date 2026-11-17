from pathlib import Path

from lab2 import CatalogError, JsonCatalogRepository, KeyboardShop, ShopCLI


def main() -> None:
    path = Path(__file__).resolve().parent / "data" / "catalog.json"
    try:
        catalog = JsonCatalogRepository(path).load()
    except CatalogError as error:
        print(f"Помилка: {error}")
        return
    try:
        ShopCLI(KeyboardShop(catalog)).run()
    except (EOFError, KeyboardInterrupt):
        print("\nПрограму завершено.")


if __name__ == "__main__":
    main()
