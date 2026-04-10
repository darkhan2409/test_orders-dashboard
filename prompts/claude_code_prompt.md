# Orders Dashboard — Подзадачи для Claude Code

Тестовое задание: система аналитики для интернет-магазина "Nova".
Выполняй шаги последовательно, каждый — отдельный промпт.

## Порядок выполнения

| Шаг | Файл | Что делает |
|-----|------|------------|
| 1 | [step1_setup.md](step1_setup.md) | Структура проекта, .env, .gitignore, requirements.txt |
| 2 | [step2_upload.md](step2_upload.md) | upload_orders.py — загрузка заказов в RetailCRM |
| 3 | [step3_supabase.md](step3_supabase.md) | SQL для создания таблиц в Supabase (orders, order_items, insights) |
| 4 | [step4_sync.md](step4_sync.md) | sync.py — RetailCRM -> Supabase |
| 5 | [step5_dashboard.md](step5_dashboard.md) | index.html — дашборд с графиками, фильтрами, CSV, AI-блоком |
| 5б | [step5b_ai_insights.md](step5b_ai_insights.md) | generate_insights.py — AI-аналитика через OpenAI API |
| 6 | [step6_telegram.md](step6_telegram.md) | telegram_bot.py — уведомления + команды /stats, /report |

## Между шагами (вручную)

- После шага 1: заполни `.env` своими данными
- После шага 2: проверь что заказы появились в RetailCRM
- После шага 3: выполни SQL в Supabase SQL Editor
- После шага 4: проверь что данные появились в Supabase
- После шага 5: открой index.html, проверь графики и фильтры
- После шага 5б: проверь что инсайты появились на дашборде
- После шага 6: проверь /stats и /report, сделай скриншот

## Финализация

- `vercel --prod` из папки `dashboard/`
- Заполни README: промпты, трудности, решения
- Отправь результаты @DmitriyKrasnikov в Telegram

## Что сдать

- Ссылка на дашборд (Vercel)
- GitHub-репозиторий с кодом
- Скриншот уведомления в Telegram
- README с промптами и описанием трудностей
