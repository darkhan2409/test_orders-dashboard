"""Обогащение utm_source в Supabase из mock_orders.json.

RetailCRM не сохранил customFields, поэтому utm_source = null в таблице orders.
Этот скрипт сопоставляет заказы по номеру телефона и проставляет utm_source.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

# --- Константы ---

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
MOCK_FILE: Path = Path(__file__).parent.parent / "mock_orders.json"


# --- Функции ---


def load_phone_utm_map(path: Path) -> dict[str, str]:
    """Строит словарь телефон -> utm_source из mock_orders.json.

    Args:
        path: Путь к файлу mock_orders.json.

    Returns:
        Словарь вида {"+77001234501": "instagram", ...}.
    """
    with open(path, encoding="utf-8") as f:
        orders = json.load(f)

    return {
        order["phone"]: order.get("customFields", {}).get("utm_source")
        for order in orders
        if order.get("phone") and order.get("customFields", {}).get("utm_source")
    }


def enrich_utm(supabase: Client, phone_utm_map: dict[str, str]) -> int:
    """Обновляет utm_source в таблице orders по номеру телефона.

    Args:
        supabase: Клиент Supabase.
        phone_utm_map: Словарь телефон -> utm_source.

    Returns:
        Количество обновлённых строк.
    """
    updated = 0
    for phone, utm_source in phone_utm_map.items():
        try:
            result = (
                supabase.table("orders")
                .update({"utm_source": utm_source})
                .eq("phone", phone)
                .execute()
            )
            if result.data:
                updated += len(result.data)
        except Exception as e:
            print(f"Ошибка при обновлении {phone}: {e}")

    return updated


def main() -> None:
    """Точка входа: обогащает utm_source в Supabase из mock_orders.json."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Ошибка: заполни SUPABASE_URL и SUPABASE_KEY в .env")
        return

    phone_utm_map = load_phone_utm_map(MOCK_FILE)
    print(f"Найдено записей в mock_orders.json: {len(phone_utm_map)}")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    updated = enrich_utm(supabase, phone_utm_map)

    print(f"Обновлено заказов: {updated}")


# --- Точка входа ---

if __name__ == "__main__":
    main()
