# Orders Dashboard — Nova Analytics

Система аналитики заказов для интернет-магазина корректирующего белья "Nova" (Казахстан).
Тестовое задание на позицию AI Tools Specialist.

## Архитектура

```
RetailCRM → sync.py → Supabase → index.html (Vercel)
                              ↑
              generate_insights.py (OpenAI GPT-4o-mini)

RetailCRM → telegram_bot.py → Telegram
Supabase  ↗
```

## Стек

| Слой | Технология |
|------|------------|
| CRM | RetailCRM API v5 |
| База данных | Supabase (PostgreSQL) |
| Фронтенд | HTML + Chart.js + Supabase JS |
| Хостинг | Vercel |
| AI | OpenAI GPT-4o-mini |
| Уведомления | Telegram Bot API |
| Язык | Python 3.11 |

## Как запустить

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Заполнить переменные окружения
cp .env.example .env
# Отредактировать .env своими данными

# 3. Загрузить заказы в RetailCRM
python scripts/upload_orders.py

# 4. Выполнить SQL в Supabase SQL Editor (создание таблиц)
# см. prompts/step3_supabase.md

# 5. Синхронизировать данные в Supabase
python scripts/sync.py

# 6. Обогатить utm_source (RetailCRM не сохраняет customFields без настройки)
python scripts/enrich_utm.py

# 7. Сгенерировать AI-инсайты
python scripts/generate_insights.py

# 8. Открыть дашборд
# Вставить SUPABASE_URL и SUPABASE_ANON_KEY в dashboard/index.html
# Открыть dashboard/index.html в браузере

# 9. Задеплоить на Vercel
vercel --prod  # из папки dashboard/

# 10. Запустить Telegram-бота
python scripts/telegram_bot.py
```

## Скрипты

| Файл | Описание |
|------|----------|
| `scripts/upload_orders.py` | Загружает 50 заказов из mock_orders.json в RetailCRM |
| `scripts/sync.py` | Синхронизирует заказы из RetailCRM в Supabase |
| `scripts/enrich_utm.py` | Обогащает utm_source по номеру телефона из mock_orders.json |
| `scripts/generate_insights.py` | Генерирует AI-рекомендации через OpenAI, сохраняет в Supabase |
| `scripts/telegram_bot.py` | Мониторинг заказов + команды /stats и /report |

## Telegram-бот команды

- `/stats` — статистика заказов из Supabase (количество, сумма, средний чек, топ город и источник)
- `/report` — AI-отчёт из таблицы insights

Автоматически: уведомление при заказе > 50 000 KZT.

## Дашборд

- 3 KPI-карточки с анимацией count-up
- Фильтры по периоду (7 / 30 / все дни) и городу
- 4 графика: заказы по дням, города, UTM-источники, топ товаров по выручке
- Блок AI-аналитики (5 рекомендаций от GPT-4o-mini)
- Кнопка экспорта в CSV

---

## Промпты которые использовал

Весь проект построен через Claude Code (claude-opus-4) с пошаговыми промптами.

### Подход

Разбил задание на 7 независимых подзадач (файлы `prompts/step*.md`), каждую выполнял отдельным промптом. Это позволило итерировать быстро и отлаживать по частям.

### Ключевые промпты

**Структура проекта:**
```
Создай структуру Python-проекта для системы аналитики заказов.
Стек: RetailCRM API, Supabase, Telegram Bot.
Файлы: upload_orders.py, sync.py, telegram_bot.py, dashboard/index.html.
Требования: type hints, докстринги на русском, try/except на верхнем уровне.
```
**Результат:** структура создана с первого раза.  
**Что поправил вручную:** ничего.

---

**Загрузка в RetailCRM:**
```
Напиши скрипт upload_orders.py который читает mock_orders.json
и загружает каждый заказ через POST /api/v5/orders/create.
Заказ передавать как data={"order": json.dumps(order)}.
Задержка 0.5 сек, прогресс в консоль, обработка ошибок.
```
**Результат:** скрипт сгенерирован с первого раза.  
**Что поправил вручную:** убрал `orderType` из payload — в демо-аккаунте RetailCRM тип `eshop-individual` не существует (см. Проблема 1).

---

**Синхронизация RetailCRM → Supabase:**
```
Напиши sync.py который забирает все заказы из RetailCRM с пагинацией
и делает upsert в Supabase таблицу orders через supabase-py.
Все credentials из .env.
```
**Результат:** сработало с первого раза.  
**Что поправил вручную:** utm_source не попал в Supabase — добавил отдельный скрипт enrich_utm.py (см. Проблема 2).

---

**AI-аналитика:**
```
Напиши скрипт generate_insights.py:
1. Загружает данные из Supabase (orders + order_items)
2. Формирует сводку: города, UTM-источники, топ товаров
3. Отправляет в OpenAI GPT-4o-mini с ролью бизнес-аналитика
4. Сохраняет 4-5 рекомендаций в таблицу insights
5. Выводит каждый инсайт в консоль
```
**Результат:** скрипт сгенерирован корректно.  
**Что поправил вручную:** настроил RLS политики в Supabase — без них INSERT блокировался (см. Проблема 5).

---

**Дашборд:**
```
Создай одностраничный дашборд dashboard/index.html.
Supabase JS + Chart.js через CDN, тёмная тема (#0f172a).
Компоненты: 3 KPI-карточки с count-up анимацией,
фильтры по периоду и городу, 4 графика, блок AI-инсайтов, CSV-экспорт.
Фильтрация в памяти (не новый запрос к Supabase).
Верификация: 50 заказов, сумма 2 451 000 KZT, средний чек 49 020 KZT.
```
**Результат:** сгенерировал с первого раза, все цифры сошлись.  
**Что поправил вручную:** ничего.

---

**Telegram-бот:**
```
Напиши telegram_bot.py с polling каждые 3 сек.
Мониторинг заказов > 50000 KZT каждые 60 сек из RetailCRM.
Команды /stats и /report из Supabase.
CHAT_ID использовать и для отправки, и как фильтр команд.
```
**Результат:** сработало с первого раза.  
**Что поправил вручную:** убедился что запущен только один экземпляр (см. Проблема 3).

---

## Где застрял и как решил

**Проблема 1: `orderType: eshop-individual` не принимался RetailCRM**  
RetailCRM вернул "Order is not loaded". Через тест выяснил что в демо-аккаунте существует только тип `main`. Решение: убирать `orderType` из payload перед отправкой — RetailCRM подставляет дефолтный тип сам.

**Проблема 2: utm_source не сохранился в RetailCRM**  
RetailCRM принял `customFields: {utm_source: "instagram"}` без ошибки, но при получении заказов `customFields` возвращался пустым — поле не было настроено в аккаунте. Решение: отдельный скрипт `enrich_utm.py` — сопоставляет заказы по телефону с mock_orders.json и обновляет utm_source напрямую в Supabase.

**Проблема 3: Telegram-бот отвечал дважды**  
При первом запуске случайно запустил два экземпляра бота одновременно. Оба получали одно обновление и оба отвечали. Решение: убедиться что запущен только один экземпляр.

**Проблема 4: Кодировка в Windows-терминале**  
Кириллица в выводе Python отображалась кракозябрами из-за cp1251. Косметическая проблема — данные в Supabase и Telegram передавались корректно (UTF-8).

**Проблема 5: RLS блокировал запись в Supabase**  
`generate_insights.py` не мог записать инсайты — Row Level Security блокировал INSERT и DELETE с anon ключом. Решение: добавил политики в SQL Editor:
```sql
create policy "Allow anon insert" on insights for insert with check (true);
create policy "Allow anon delete" on insights for delete using (true);
```

---

## Заметки по безопасности

`SUPABASE_ANON_KEY` захардкожен в `dashboard/index.html` намеренно — для демо.  
В продакшене выносится в переменные окружения Vercel и подставляется через build step.  
`SUPABASE_SERVICE_KEY` используется только в серверном коде (Python скрипты и Vercel serverless function) и никогда не попадает на фронтенд.

---

## Результаты

- Дашборд: [https://test-orders-dashboard.vercel.app/]
- Репо: [https://github.com/darkhan2409/test_orders-dashboard]
- Скриншот RetailCRM: см. `screenshots/screen_1.PNG`
- Скриншот Telegram уведомления: см. `screenshots/screen_2.PNG`
