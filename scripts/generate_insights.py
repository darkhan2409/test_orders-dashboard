"""Генерация AI-инсайтов по данным заказов через OpenAI API."""

import os
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

# --- Константы ---

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
MODEL: str = "gpt-4o-mini"


# --- Функции ---


def fetch_data(supabase: Client) -> tuple[list[dict], list[dict]]:
    """Загружает заказы и товары из Supabase.

    Args:
        supabase: Клиент Supabase.

    Returns:
        Кортеж (список заказов, список товаров).
    """
    orders = supabase.table("orders").select("*").execute().data or []
    items = supabase.table("order_items").select("*").execute().data or []
    return orders, items


def build_summary(orders: list[dict], items: list[dict]) -> str:
    """Формирует текстовую сводку данных для передачи в OpenAI.

    Args:
        orders: Список заказов из таблицы orders.
        items: Список товаров из таблицы order_items.

    Returns:
        Строка с аналитической сводкой.
    """
    total_count = len(orders)
    total_sum = sum(o.get("total", 0) or 0 for o in orders)
    avg_check = round(total_sum / total_count) if total_count else 0

    # Группировка по городам
    cities: dict[str, dict] = defaultdict(lambda: {"count": 0, "sum": 0})
    for o in orders:
        city = o.get("city") or "Не указан"
        cities[city]["count"] += 1
        cities[city]["sum"] += o.get("total", 0) or 0

    # Группировка по UTM-источникам
    utms: dict[str, dict] = defaultdict(lambda: {"count": 0, "sum": 0})
    for o in orders:
        utm = o.get("utm_source") or "Не указан"
        utms[utm]["count"] += 1
        utms[utm]["sum"] += o.get("total", 0) or 0

    # Группировка по товарам
    products: dict[str, dict] = defaultdict(lambda: {"qty": 0, "revenue": 0})
    for item in items:
        name = item.get("product_name") or "Неизвестно"
        products[name]["qty"] += item.get("quantity", 0)
        products[name]["revenue"] += (item.get("price", 0) or 0) * (item.get("quantity", 0) or 0)

    # Формируем текст сводки
    cities_text = "\n".join(
        f"  - {city}: {d['count']} заказов, {d['sum']:,} KZT"
        for city, d in sorted(cities.items(), key=lambda x: -x[1]["count"])
    )
    utms_text = "\n".join(
        f"  - {utm}: {d['count']} заказов, {d['sum']:,} KZT"
        for utm, d in sorted(utms.items(), key=lambda x: -x[1]["count"])
    )
    products_text = "\n".join(
        f"  - {name}: {d['qty']} шт., выручка {d['revenue']:,} KZT"
        for name, d in sorted(products.items(), key=lambda x: -x[1]["revenue"])
    )

    return f"""Данные магазина Nova (корректирующее бельё, Казахстан):

Общая статистика:
  - Заказов: {total_count}
  - Общая сумма: {total_sum:,} KZT
  - Средний чек: {avg_check:,} KZT

Города:
{cities_text}

Источники трафика (UTM):
{utms_text}

Топ товаров:
{products_text}"""


def generate_insights(summary: str, client: OpenAI) -> list[str]:
    """Отправляет сводку в OpenAI и получает список бизнес-рекомендаций.

    Args:
        summary: Текстовая сводка аналитических данных.
        client: Клиент OpenAI.

    Returns:
        Список строк — каждая строка одна рекомендация.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — бизнес-аналитик интернет-магазина корректирующего белья 'Nova' (Казахстан). "
                    "Проанализируй данные заказов и дай 4-5 конкретных бизнес-рекомендаций. "
                    "Каждая рекомендация — 1-2 предложения с конкретными цифрами из данных. "
                    "Начинай каждую рекомендацию с короткого заголовка (3-5 слов), затем двоеточие и текст. "
                    "Пиши на русском. Каждая рекомендация на новой строке."
                ),
            },
            {"role": "user", "content": summary},
        ],
        temperature=0.7,
    )

    text = response.choices[0].message.content or ""
    # Разбиваем по строкам, убираем пустые
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def save_insights(supabase: Client, insights: list[str]) -> None:
    """Очищает старые инсайты и сохраняет новые в Supabase.

    Args:
        supabase: Клиент Supabase.
        insights: Список текстов рекомендаций.
    """
    supabase.table("insights").delete().neq("id", 0).execute()
    rows = [{"content": text} for text in insights]
    supabase.table("insights").insert(rows).execute()


def main() -> None:
    """Точка входа: генерирует AI-инсайты и сохраняет в Supabase."""
    if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
        print("Ошибка: заполни SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY в .env")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    print("Загружаю данные из Supabase...")
    try:
        orders, items = fetch_data(supabase)
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return

    print(f"Заказов: {len(orders)}, товаров: {len(items)}")

    summary = build_summary(orders, items)

    print("Отправляю в OpenAI...")
    try:
        insights = generate_insights(summary, openai_client)
    except Exception as e:
        print(f"Ошибка OpenAI: {e}")
        return

    print("Сохраняю в Supabase...")
    try:
        save_insights(supabase, insights)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return

    print(f"\nСгенерировано {len(insights)} инсайтов:\n")
    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")


# --- Точка входа ---

if __name__ == "__main__":
    main()
