"""Синхронизация заказов из RetailCRM в Supabase."""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Константы ---

load_dotenv()

API_URL: str = os.getenv("RETAILCRM_URL", "")
API_KEY: str = os.getenv("RETAILCRM_API_KEY", "")
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

PAGE_LIMIT: int = 50  # допустимые значения: 20, 50, 100


# --- Функции ---


def fetch_orders_page(page: int) -> dict:
    """Загружает одну страницу заказов из RetailCRM.

    Args:
        page: Номер страницы (начиная с 1).

    Returns:
        Словарь с ключами 'orders' и 'pagination' из ответа API.
    """
    response = requests.get(
        f"{API_URL}/api/v5/orders",
        params={"apiKey": API_KEY, "limit": PAGE_LIMIT, "page": page},
        timeout=15,
    )
    return response.json()


def fetch_all_orders() -> list[dict]:
    """Загружает все заказы из RetailCRM постранично.

    Returns:
        Список всех заказов.
    """
    all_orders = []
    page = 1

    while True:
        data = fetch_orders_page(page)
        if not data.get("success"):
            print(f"Ошибка RetailCRM: {data.get('errorMsg')}")
            break

        orders = data.get("orders", [])
        all_orders.extend(orders)

        pagination = data.get("pagination", {})
        total_pages = pagination.get("totalPageCount", 1)
        print(f"Страница {page}/{total_pages}, заказов на странице: {len(orders)}")

        if page >= total_pages:
            break
        page += 1

    return all_orders


def map_order(order: dict) -> dict:
    """Преобразует заказ из формата RetailCRM в формат таблицы orders.

    Args:
        order: Заказ из ответа RetailCRM API.

    Returns:
        Словарь для вставки в таблицу orders.
    """
    # Сумма заказа: sum(initialPrice * quantity) по всем позициям
    items = order.get("items", [])
    total = sum(
        item.get("initialPrice", 0) * item.get("quantity", 0)
        for item in items
    )

    # utm_source хранится в customFields, но может быть пустым если поле не настроено в CRM
    custom_fields = order.get("customFields", {})
    utm_source = None
    if isinstance(custom_fields, dict):
        utm_source = custom_fields.get("utm_source")

    return {
        "id": str(order["id"]),
        "number": order.get("number"),
        "status": order.get("status"),
        "total": total,
        "created_at": order.get("createdAt"),
        "customer_name": f"{order.get('firstName', '')} {order.get('lastName', '')}".strip(),
        "phone": order.get("phone"),
        "email": order.get("email"),
        "city": order.get("delivery", {}).get("address", {}).get("city"),
        "utm_source": utm_source,
    }


def map_items(order_id: str, items: list[dict]) -> list[dict]:
    """Преобразует позиции заказа в формат таблицы order_items.

    Args:
        order_id: ID заказа (строка).
        items: Список позиций из ответа RetailCRM.

    Returns:
        Список словарей для вставки в таблицу order_items.
    """
    result = []
    for item in items:
        # Название товара находится в offer.name
        product_name = item.get("offer", {}).get("name") or item.get("productName")
        result.append({
            "order_id": order_id,
            "product_name": product_name,
            "quantity": item.get("quantity", 0),
            "price": item.get("initialPrice", 0),
        })
    return result


def sync_to_supabase(supabase: Client, orders: list[dict]) -> tuple[int, int]:
    """Вставляет заказы и их товары в Supabase через upsert.

    Args:
        supabase: Клиент Supabase.
        orders: Список заказов из RetailCRM.

    Returns:
        Кортеж (количество заказов, количество товаров).
    """
    order_count = 0
    item_count = 0

    for order in orders:
        try:
            order_row = map_order(order)
            order_id = order_row["id"]

            # Upsert заказа
            supabase.table("orders").upsert(order_row, on_conflict="id").execute()
            order_count += 1

            # Удаляем старые товары этого заказа, затем вставляем новые
            items = order.get("items", [])
            if items:
                supabase.table("order_items").delete().eq("order_id", order_id).execute()
                item_rows = map_items(order_id, items)
                supabase.table("order_items").insert(item_rows).execute()
                item_count += len(item_rows)

        except Exception as e:
            print(f"Ошибка при обработке заказа {order.get('id')}: {e}")
            continue

    return order_count, item_count


def main() -> None:
    """Точка входа: синхронизирует заказы из RetailCRM в Supabase."""
    if not all([API_URL, API_KEY, SUPABASE_URL, SUPABASE_KEY]):
        print("Ошибка: проверь RETAILCRM_URL, RETAILCRM_API_KEY, SUPABASE_URL, SUPABASE_KEY в .env")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Загружаю заказы из RetailCRM...")
    try:
        orders = fetch_all_orders()
    except Exception as e:
        print(f"Ошибка при загрузке из RetailCRM: {e}")
        return

    print(f"Получено заказов: {len(orders)}. Синхронизирую в Supabase...")
    order_count, item_count = sync_to_supabase(supabase, orders)

    print(f"Синхронизировано {order_count} заказов, {item_count} товаров")


# --- Точка входа ---

if __name__ == "__main__":
    main()
