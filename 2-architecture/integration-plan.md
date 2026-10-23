# План інтеграції

## Порядок інтеграції

Знизу вгору, щоб кожен крок перевірявся без зовнішнього API і без грошей:

| Крок | Що інтегруємо | Чим заміняємо відсутнє | Перевірка |
|---|---|---|---|
| 1 | Конфігурація + M4 Промпт | — | TC-11 |
| 2 | M5 LLM-адаптер із заглушкою (`MockGenerator`) | Gemini → заглушка | TC-16…TC-22 (фейковий клієнт) |
| 3 | M3 HTTP API + M5 | Gemini → заглушка | TC-01…TC-15 |
| 4 | M2 API-клієнт + M1 UI | бекенд → підмінений `fetch` | TC-23…TC-27 |
| 5 | Фронтенд + бекенд через проксі Vite | Gemini → `LLM_PROVIDER=mock` | ручний прохід UC-01 |
| 6 | Бекенд + справжній Gemini | — | TC-32…TC-34 |
| 7 | nginx + Docker Compose | — | `docker compose up`, `/api/health` |
| 8 (v0.3) | M6 Сховище + PostgreSQL | — | інтеграційні тести з тестовою БД |

## Сценарій 1. Успішна генерація

```mermaid
sequenceDiagram
    autonumber
    actor U as Користувач
    participant UI as M1 UI (React)
    participant C as M2 API-клієнт
    participant N as nginx
    participant A as M3 HTTP API
    participant L as M5 LLM-адаптер
    participant P as M4 Промпт
    participant G as Gemini API

    U->>UI: імʼя «Саша», стиль «Брейнрот», «Згенерувати»
    UI->>UI: стан loading, кнопка «Генеруємо…»
    UI->>C: generateGreeting({name, style})
    C->>N: POST /api/greetings
    N->>A: proxy_pass
    A->>A: валідація (обрізати пробіли, 1–50 символів)
    A->>A: зайняти слот (Semaphore 20)
    A->>L: generate("Саша", brainrot)
    L->>P: build_user_prompt()
    P-->>L: промпт
    L->>G: generate_content(model, prompt, system, timeout 15 с)
    G-->>L: текст + usage
    L-->>A: текст
    A-->>N: 200 {text, style}
    N-->>C: 200
    C-->>UI: {text}
    UI-->>U: привітання на сторінці
```

## Сценарій 2. Збій провайдера і повтор

```mermaid
sequenceDiagram
    autonumber
    actor U as Користувач
    participant UI as M1 UI
    participant C as M2 API-клієнт
    participant A as M3 HTTP API
    participant L as M5 LLM-адаптер
    participant G as Gemini API

    U->>UI: «Згенерувати»
    UI->>C: generateGreeting()
    C->>A: POST /api/greetings
    A->>L: generate()
    L->>G: generate_content (спроба 1)
    G-->>L: 504 DEADLINE_EXCEEDED
    L->>G: повтор через ~2 с (спроба 2)
    G-->>L: 504 DEADLINE_EXCEEDED
    L-->>A: LLMUnavailable
    A-->>C: 503 {"detail": "Сервіс генерації тимчасово недоступний"}
    C-->>UI: ApiError(503)
    UI-->>U: повідомлення + «Повторити»
    U->>UI: «Повторити»
    UI->>C: generateGreeting() з тими самими параметрами
    C->>A: POST /api/greetings
    A->>L: generate()
    L->>G: generate_content
    G-->>L: текст
    A-->>C: 200 {text}
    UI-->>U: привітання, повідомлення зникло
```

Цей сценарій реально спостерігався 19.10.2026 ([test-report.md](../4-quality/test-report.md)).

## Стики модулів і можливі проблеми

| Стик | Ризик | Як захищено | Стан |
|---|---|---|---|
| M1 ↔ M2 | UI чекає поле `text`, а сервер змінить формат | спільний контракт [api.md](api.md); TC-25 | ✅ |
| M2 ↔ M3 (браузер ↔ сервер) | CORS-блокування; різні URL у dev і prod | у dev — проксі Vite, у prod — nginx на тому ж домені; `CORS_ORIGINS` у `.env`; TC-15 | ✅ |
| M2 ↔ M3: помилка валідації 422 | `detail` — масив, а не рядок; користувач бачить загальне повідомлення | BUG-05 | ⚠️ |
| M3 ↔ M5 | винятки провайдера «протікають» як 500 | адаптер перетворює все на `LLMBusy` / `LLMUnavailable` → 429 / 503; TC-12…TC-20 | ✅ |
| M5 ↔ Gemini: час | відповідь > 10 с або 504 | таймаут 15 с + 1 повтор; BUG-03 | ❌ NFR-1 |
| M5 ↔ Gemini: ліміти | 429 від безкоштовного тарифу | → 429 «спробуйте за хвилину»; TC-17 | ✅ |
| M5 ↔ Gemini: фільтр безпеки | `text = None` | → 503; з v0.2 — повторна генерація (FR-15) | ⚠️ |
| M5 ↔ Gemini: мова | імʼя в кличному відмінку («Сашо») ламає наївну перевірку | критерій FR-03 уточнено (CR-04) | ✅ |
| nginx ↔ M3 | nginx обірве довгий запит раніше за бекенд | `proxy_read_timeout 40s` > найгірший час бекенду (2 × 15 с + пауза) | ✅ |
| Воркери Uvicorn ↔ ліміт одночасних викликів | `Semaphore` у кожному процесі окремо: 2 воркери → 40 викликів | BUG-04 | ⚠️ |
| Конфігурація ↔ `.env` | немає ключа → незрозуміле падіння | явна помилка з посиланням на AI Studio при старті; TC-21 | ✅ |
