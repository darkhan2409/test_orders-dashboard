# Шаг 1: Структура проекта и настройка

Я делаю тестовое задание — систему аналитики для интернет-магазина "Nova".

Создай структуру проекта в текущей корневой папке и базовые конфигурационные файлы.

## Структура

```
.env.example
.gitignore
requirements.txt
scripts/
dashboard/
mock_orders.json    # уже есть
README.md
```

## Файлы для создания

### .env.example

```
RETAILCRM_URL=https://ВАШ_АККАУНТ.retailcrm.ru
RETAILCRM_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
OPENAI_API_KEY=

```

### .gitignore

```
node_modules/
.env
.env.local
__pycache__/
*.pyc
.venv/
venv/
.DS_Store
.vercel/
```

### requirements.txt

```
requests
supabase
python-dotenv
openai
```

### mock_orders.json

НЕ создавай — файл уже есть в корневой папке.

### README.md

Создай пустой файл-заглушку, содержимое заполним позже.

```markdown
# Orders Dashboard — Nova Analytics
```

## Требования к коду

- Комментарии на русском
- Никаких эмодзи
