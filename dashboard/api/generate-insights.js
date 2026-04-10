/**
 * Vercel Serverless Function: генерация AI-инсайтов.
 * Ключи читаются из переменных окружения Vercel — никогда не попадают на клиент.
 */

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

const SYSTEM_PROMPT =
  'Ты — бизнес-аналитик интернет-магазина корректирующего белья "Nova" (Казахстан). ' +
  'Проанализируй данные заказов и дай 4-5 конкретных бизнес-рекомендаций. ' +
  'Каждая рекомендация — 1-2 предложения с конкретными цифрами из данных. ' +
  'Начинай каждую рекомендацию с короткого заголовка (3-5 слов), затем двоеточие и текст. ' +
  'Пиши на русском. Каждая рекомендация на новой строке.';

/** Запрос к Supabase REST API */
async function supabaseFetch(path, options = {}) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...options,
    headers: {
      apikey: SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_KEY}`,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Supabase ${path}: ${res.status} ${text}`);
  }
  return options.method && options.method !== 'GET' ? null : res.json();
}

/** Строит текстовую сводку для промпта */
function buildSummary(orders, items) {
  const count = orders.length;
  const totalSum = orders.reduce((s, o) => s + (o.total || 0), 0);
  const avg = count ? Math.round(totalSum / count) : 0;

  const group = (arr, key) =>
    arr.reduce((acc, o) => {
      const k = o[key] || 'Не указан';
      if (!acc[k]) acc[k] = { count: 0, sum: 0 };
      acc[k].count++;
      acc[k].sum += o.total || 0;
      return acc;
    }, {});

  const fmt = (n) => n.toLocaleString('ru-RU');

  const citiesText = Object.entries(group(orders, 'city'))
    .sort((a, b) => b[1].count - a[1].count)
    .map(([c, d]) => `  - ${c}: ${d.count} заказов, ${fmt(d.sum)} KZT`)
    .join('\n');

  const utmsText = Object.entries(group(orders, 'utm_source'))
    .sort((a, b) => b[1].count - a[1].count)
    .map(([u, d]) => `  - ${u}: ${d.count} заказов, ${fmt(d.sum)} KZT`)
    .join('\n');

  const products = items.reduce((acc, i) => {
    const n = i.product_name || 'Неизвестно';
    if (!acc[n]) acc[n] = { qty: 0, revenue: 0 };
    acc[n].qty += i.quantity || 0;
    acc[n].revenue += (i.price || 0) * (i.quantity || 0);
    return acc;
  }, {});

  const productsText = Object.entries(products)
    .sort((a, b) => b[1].revenue - a[1].revenue)
    .map(([n, d]) => `  - ${n}: ${d.qty} шт., выручка ${fmt(d.revenue)} KZT`)
    .join('\n');

  return `Данные магазина Nova (корректирующее бельё, Казахстан):

Общая статистика:
  - Заказов: ${count}
  - Общая сумма: ${fmt(totalSum)} KZT
  - Средний чек: ${fmt(avg)} KZT

Города:
${citiesText}

Источники трафика (UTM):
${utmsText}

Топ товаров:
${productsText}`;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!OPENAI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return res.status(500).json({ error: 'Не заданы переменные окружения на сервере' });
  }

  try {
    // Загрузить данные из Supabase
    const [orders, items] = await Promise.all([
      supabaseFetch('orders?select=total,city,utm_source'),
      supabaseFetch('order_items?select=product_name,quantity,price'),
    ]);

    const summary = buildSummary(orders, items);

    // Вызвать OpenAI
    const aiRes = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        temperature: 0.7,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: summary },
        ],
      }),
    });

    if (!aiRes.ok) {
      const err = await aiRes.json().catch(() => ({}));
      return res.status(502).json({ error: err.error?.message || 'Ошибка OpenAI' });
    }

    const aiJson = await aiRes.json();
    const lines = aiJson.choices[0].message.content
      .trim()
      .split('\n')
      .filter((l) => l.trim());

    // Обновить таблицу insights
    await supabaseFetch('insights?id=neq.0', { method: 'DELETE' });
    await supabaseFetch('insights', {
      method: 'POST',
      body: JSON.stringify(lines.map((content) => ({ content }))),
    });

    // Вернуть свежие инсайты
    const fresh = await supabaseFetch(
      'insights?select=*&order=generated_at.desc'
    );
    return res.status(200).json({ insights: fresh });

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
