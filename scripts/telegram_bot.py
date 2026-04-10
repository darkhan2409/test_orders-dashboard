"""Telegram-бот: мониторинг заказов Nova + команды /stats и /report."""

import os
import time
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Константы ---

load_dotenv()

RETAILCRM_URL: str = os.getenv("RETAILCRM_URL", "")
RETAILCRM_API_KEY: str = os.getenv("RETAILCRM_API_KEY", "")
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

TG_API: str = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
ORDER_THRESHOLD: int = 50_000  # KZT
CHECK_INTERVAL: int = 60       # секунды между проверками RetailCRM
POLL_TIMEOUT: int = 3          # секунды ожидания в getUpdates


# --- Telegram-функции ---


def send_message(text: str, parse_mode: str = "HTML") -> None:
    """Отправляет сообщение в чат.

    Args:
        text: Текст сообщения.
        parse_mode: Режим разметки (HTML или Markdown).
    """
    try:
        requests.post(
            f"{TG_API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode},
            timeout=10,
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")


def get_updates(offset: int) -> list[dict]:
    """Получает новые сообщения от Telegram через long polling.

    Args:
        offset: ID последнего обработанного update + 1.

    Returns:
        Список объектов update от Telegram.
    """
    try:
        resp = requests.get(
            f"{TG_API}/getUpdates",
            params={"offset": offset, "timeout": POLL_TIMEOUT},
            timeout=POLL_TIMEOUT + 5,
        )
        return resp.json().get("result", [])
    except Exception as e:
        print(f"Ошибка getUpdates: {e}")
        return []


# --- Мониторинг RetailCRM ---


def check_new_orders(sent_ids: set) -> set:
    """Проверяет новые заказы в RetailCRM за последний час.

    Отправляет уведомление если сумма заказа > ORDER_THRESHOLD и заказ ещё не отправлялся.

    Args:
        sent_ids: Множество ID уже отправленных заказов.

    Returns:
        Обновлённое множество sent_ids.
    """
    from_dt = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        resp = requests.get(
            f"{RETAILCRM_URL}/api/v5/orders",
            params={
                "apiKey": RETAILCRM_API_KEY,
                "limit": 100,
                "page": 1,
                "filter[createdAtFrom]": from_dt,
            },
            timeout=15,
        )
        data = resp.json()
        if not data.get("success"):
            print(f"Ошибка RetailCRM: {data.get('errorMsg')}")
            return sent_ids

        for order in data.get("orders", []):
            order_id = order.get("id")
            if order_id in sent_ids:
                continue

            items = order.get("items", [])
            total = sum(
                item.get("initialPrice", 0) * item.get("quantity", 0)
                for item in items
            )

            if total > ORDER_THRESHOLD:
                number = order.get("number", "?")
                name = f"{order.get('firstName', '')} {order.get('lastName', '')}".strip()
                city = order.get("delivery", {}).get("address", {}).get("city", "Не указан")

                text = (
                    f"<b>Новый заказ #{number}</b>\n"
                    f"Сумма: <b>{total:,} KZT</b>\n"
                    f"Клиент: {name}\n"
                    f"Город: {city}"
                )
                send_message(text)
                sent_ids.add(order_id)
                print(f"Отправлено уведомление: заказ #{number}, {total:,} KZT")

    except Exception as e:
        print(f"Ошибка при проверке заказов: {e}")

    return sent_ids


# --- Команды ---


def cmd_stats(supabase: Client) -> None:
    """Отправляет статистику заказов из Supabase.

    Args:
        supabase: Клиент Supabase.
    """
    try:
        orders = supabase.table("orders").select("total, city, utm_source").execute().data or []

        count = len(orders)
        total_sum = sum(o.get("total", 0) or 0 for o in orders)
        avg = round(total_sum / count) if count else 0

        # Топ город
        cities: dict[str, int] = {}
        for o in orders:
            c = o.get("city") or "Не указан"
            cities[c] = cities.get(c, 0) + 1
        top_city = max(cities, key=lambda c: cities[c]) if cities else "-"

        # Топ UTM
        utms: dict[str, int] = {}
        for o in orders:
            u = o.get("utm_source") or "Не указан"
            utms[u] = utms.get(u, 0) + 1
        top_utm = max(utms, key=lambda u: utms[u]) if utms else "-"

        text = (
            f"<b>Статистика Nova</b>\n\n"
            f"Заказов: {count}\n"
            f"Общая сумма: {total_sum:,} KZT\n"
            f"Средний чек: {avg:,} KZT\n"
            f"Топ город: {top_city} ({cities.get(top_city, 0)})\n"
            f"Топ источник: {top_utm} ({utms.get(top_utm, 0)})"
        )
        send_message(text)

    except Exception as e:
        print(f"Ошибка /stats: {e}")
        send_message("Ошибка при получении статистики.")


def cmd_report(supabase: Client) -> None:
    """Отправляет AI-отчёт из таблицы insights.

    Args:
        supabase: Клиент Supabase.
    """
    try:
        insights = (
            supabase.table("insights")
            .select("content, generated_at")
            .order("generated_at", desc=True)
            .execute()
            .data or []
        )

        if not insights:
            send_message("Отчёт ещё не сгенерирован. Запустите generate_insights.py")
            return

        generated_at = insights[0].get("generated_at", "")
        date_str = generated_at[:16].replace("T", " ") if generated_at else ""

        lines = "\n\n".join(i["content"] for i in insights)
        text = f"<b>AI-отчёт</b>\n<i>Сгенерировано: {date_str}</i>\n\n{lines}"
        send_message(text)

    except Exception as e:
        print(f"Ошибка /report: {e}")
        send_message("Ошибка при получении отчёта.")


# --- Основной цикл ---


def main() -> None:
    """Точка входа: запускает бота с polling и мониторингом заказов."""
    if not all([RETAILCRM_URL, RETAILCRM_API_KEY, SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN, CHAT_ID]):
        print("Ошибка: проверь все переменные в .env")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    sent_ids: set = set()
    offset: int = 0
    last_check: float = 0  # время последней проверки RetailCRM
    processed_msg_ids: set = set()  # защита от двойной обработки сообщений

    print("Бот запущен. Проверяю заказы каждые 60 секунд...")

    while True:
        # Проверка новых заказов по таймеру
        if time.time() - last_check >= CHECK_INTERVAL:
            sent_ids = check_new_orders(sent_ids)
            last_check = time.time()

        # Обработка команд
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message", {})
            msg_id = message.get("message_id")
            text = message.get("text", "").strip()
            chat_id = str(message.get("chat", {}).get("id", ""))

            # Пропускаем уже обработанные сообщения и чужие чаты
            if msg_id in processed_msg_ids or chat_id != CHAT_ID:
                continue
            processed_msg_ids.add(msg_id)

            if text == "/stats":
                print("Команда /stats")
                cmd_stats(supabase)
            elif text == "/report":
                print("Команда /report")
                cmd_report(supabase)


# --- Точка входа ---

if __name__ == "__main__":
    main()
