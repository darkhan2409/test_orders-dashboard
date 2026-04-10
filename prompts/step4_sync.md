# Шаг 4: Синхронизация RetailCRM -> Supabase

Создай файл `scripts/sync.py`.

## Что делает скрипт

Забирает все заказы из RetailCRM и сохраняет их в Supabase (таблицы `orders` и `order_items`).

## Логика

1. Запросить заказы из RetailCRM: `GET {RETAILCRM_URL}/api/v5/orders?apiKey=...`
2. Поддержать пагинацию (параметр `page`, пока есть следующая страница)
3. Для каждого заказа из ответа сформировать запись:
   - `id` — из поля `id` ответа RetailCRM (строка)
   - `number` — из поля `number`
   - `status` — из поля `status`
   - `total` — вычислить: `sum(item.quantity * item.initialPrice)` по всем items
   - `created_at` — из поля `createdAt`
   - `customer_name` — `firstName + " " + lastName`
   - `phone` — из поля `phone` (или из customer)
   - `email` — из поля `email` (или из customer)
   - `city` — из `delivery.address.city`
   - `utm_source` — из `customFields.utm_source`
4. Вставить в Supabase таблицу `orders` через **upsert** (on conflict по `id`)
5. Для каждого заказа вставить его товары в таблицу `order_items`:
   - `order_id` — id заказа
   - `product_name` — из `productName`
   - `quantity` — из `quantity`
   - `price` — из `initialPrice`
   - Перед вставкой удалить старые items этого заказа (чтобы не дублировать)
6. В конце вывести: `Синхронизировано X заказов, Y товаров`

## Credentials

Читать из `.env`:
- `RETAILCRM_URL`
- `RETAILCRM_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`

## Зависимости

- `requests` — для RetailCRM API
- `supabase` — для Supabase
- `python-dotenv` — для .env

## Требования к коду

- Type hints на всех функциях
- Докстринги на русском (описание + Args + Returns)
- Комментарии только там где неочевидно
- Обработка ошибок через try/except — при ошибке вывести и продолжить
- Никаких эмодзи
- Порядок в файле: импорты -> константы -> функции -> точка входа
