# Шаг 2: Загрузка заказов в RetailCRM

Создай файл `scripts/upload_orders.py`.

## Что делает скрипт

Читает `mock_orders.json` из корневой папки и загружает каждый заказ в RetailCRM через API.

## Структура данных в mock_orders.json

Каждый заказ выглядит так:
```json
{
  "firstName": "Айгуль",
  "lastName": "Касымова",
  "phone": "+77001234501",
  "email": "aigul.kasymova@example.com",
  "orderType": "eshop-individual",
  "orderMethod": "shopping-cart",
  "status": "new",
  "items": [
    { "productName": "Корректирующее бельё Nova Classic", "quantity": 1, "initialPrice": 15000 }
  ],
  "delivery": {
    "address": { "city": "Алматы", "text": "ул. Абая 150, кв 12" }
  },
  "customFields": { "utm_source": "instagram" }
}
```

## Требования

- Endpoint: `POST {RETAILCRM_URL}/api/v5/orders/create`
- API-ключ передавать в query-параметре: `?apiKey=...`
- Каждый заказ передавать в теле запроса как `data={"order": json.dumps(order_obj)}`
- Задержка 0.5 сек между запросами
- Прогресс в консоль: `Загружен 1/50`, `Загружен 2/50`...
- При ошибке — вывести текст ошибки и продолжить (не останавливать скрипт)
- `RETAILCRM_URL` и `RETAILCRM_API_KEY` читать из `.env` через `python-dotenv`

## Пример запроса

```python
import json, requests

data = {
    "order": json.dumps(order)
}
response = requests.post(
    f"{API_URL}/api/v5/orders/create",
    params={"apiKey": API_KEY},
    data=data
)
```

## Требования к коду

- Type hints на всех функциях
- Докстринги на русском (описание + Args + Returns)
- Комментарии только там где неочевидно
- Обработка ошибок через try/except
- Никаких эмодзи
- Порядок в файле: импорты -> константы -> функции -> точка входа
