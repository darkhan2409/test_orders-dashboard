"""Загрузка тестовых заказов из mock_orders.json в RetailCRM."""

import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

# --- Константы ---

load_dotenv()

API_URL: str = os.getenv("RETAILCRM_URL", "")
API_KEY: str = os.getenv("RETAILCRM_API_KEY", "")
MOCK_FILE: Path = Path(__file__).parent.parent / "mock_orders.json"
REQUEST_DELAY: float = 0.5  # секунды между запросами


# --- Функции ---


def load_orders(path: Path) -> list[dict]:
    """Читает список заказов из JSON-файла.

    Args:
        path: Путь к файлу mock_orders.json.

    Returns:
        Список словарей с данными заказов.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def upload_order(order: dict, index: int, total: int) -> bool:
    """Отправляет один заказ в RetailCRM через API.

    Args:
        order: Словарь с данными заказа (формат RetailCRM).
        index: Порядковый номер заказа (для вывода прогресса).
        total: Общее количество заказов.

    Returns:
        True если загружен успешно, False при ошибке.
    """
    # orderType eshop-individual не настроен в демо-аккаунте — убираем поле
    payload = {k: v for k, v in order.items() if k != "orderType"}

    try:
        response = requests.post(
            f"{API_URL}/api/v5/orders/create",
            params={"apiKey": API_KEY},
            data={"order": json.dumps(payload, ensure_ascii=False)},
            timeout=10,
        )
        result = response.json()

        if result.get("success"):
            print(f"Загружен {index}/{total} — заказ #{result.get('id', '?')}")
            return True
        else:
            print(f"Ошибка {index}/{total}: {result.get('errorMsg', result)}")
            return False

    except requests.RequestException as e:
        print(f"Ошибка сети {index}/{total}: {e}")
        return False
    except Exception as e:
        print(f"Ошибка {index}/{total}: {e}")
        return False


def main() -> None:
    """Точка входа: загружает все заказы из mock_orders.json в RetailCRM."""
    if not API_URL or not API_KEY:
        print("Ошибка: заполни RETAILCRM_URL и RETAILCRM_API_KEY в .env")
        return

    orders = load_orders(MOCK_FILE)
    total = len(orders)
    print(f"Найдено заказов: {total}. Начинаю загрузку...")

    success_count = 0
    for i, order in enumerate(orders, start=1):
        if upload_order(order, i, total):
            success_count += 1
        time.sleep(REQUEST_DELAY)

    print(f"\nГотово: загружено {success_count}/{total} заказов")


# --- Точка входа ---

if __name__ == "__main__":
    main()
