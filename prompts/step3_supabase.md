# Шаг 3: Настройка Supabase

Выведи SQL-скрипт, который нужно выполнить в Supabase SQL Editor для создания таблиц.

## Таблицы

### orders — заказы

| Поле | Тип | Описание |
|------|-----|----------|
| id | text, primary key | ID заказа из RetailCRM |
| number | text | Номер заказа |
| status | text | Статус (new, in_progress, completed, cancelled) |
| total | numeric | Сумма заказа (вычисляется из items) |
| created_at | timestamp | Дата создания (из RetailCRM) |
| customer_name | text | Имя + Фамилия |
| phone | text | Телефон |
| email | text | Email |
| city | text | Город доставки |
| utm_source | text | Источник трафика |
| synced_at | timestamp, default now() | Дата синхронизации |

### order_items — товары в заказах

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint, auto-generated | PK |
| order_id | text, FK -> orders.id | Связь с заказом |
| product_name | text | Название товара |
| quantity | int | Количество |
| price | numeric | Цена за единицу |

### insights — AI-аналитика

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint, auto-generated | PK |
| content | text | Текст инсайта / рекомендации |
| generated_at | timestamp, default now() | Когда сгенерировано |

## Также нужно

- Включить Row Level Security (RLS) на всех трёх таблицах
- Создать политику `"Allow public read"` для SELECT — чтобы дашборд мог читать данные через anon-ключ

## Формат ответа

Выведи готовый SQL-скрипт одним блоком, который я скопирую и вставлю в Supabase SQL Editor.
