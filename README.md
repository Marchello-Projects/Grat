# 🎂 ДРбот — ШІ-привітання з днем народження

- **Проблема:** вигадати оригінальне привітання з ДН — ~10 хвилин, шаблони з інтернету нудні, а жарт легко перетворити на образу.
- **Для кого:** студенти й молодь, які вітають друзів, одногрупників і колег у месенджерах.
- **Рішення:** вебзастосунок — вводите імʼя, обираєте стиль гумору (брейнрот, душевно, офіційно) і за кілька секунд отримуєте готове привітання українською.
- **Прототип:** робочий застосунок у цьому репозиторії; скриншоти — [2-architecture/prototype](2-architecture/prototype/README.md).
- **Команда:** Аліна Горбаньова — капітан і автор ідеї (власник продукту, аналітик, PM) · Марк Паскалов — розробник (архітектура, бекенд, фронтенд, DevOps) · Макс Сахошко — тестувальник.
- **Стан:** v0.1.0 — MVP працює; відкритий дефект часу відповіді ([BUG-03](4-quality/bug-reports.md)).
- **Як працювати в команді:** [CONTRIBUTING.md](CONTRIBUTING.md).
- **Беклог:** [1-lifecycle/backlog.md](1-lifecycle/backlog.md) (перенести в GitHub Projects).
- **Зміст репозиторію:** документація за темами курсу ТСПП (таблиця нижче) + код `backend/`, `frontend/`.

## Модулі консольного інкремента

Одна людина — один модуль і його тести. Спільний шар запуску — `backend/app/cli.py`. Контракт — у [практичній 4](practicals/04-repo-process.md).

| Хто | Модуль | Що працює через два тижні |
|---|---|---|

## Документація

| Тема | Документи |
|---|---|
| [0-product](0-product/) — ідея | [vision](0-product/vision.md) · [competitors](0-product/competitors.md) · [personas](0-product/personas.md) · [interviews](0-product/interviews.md) (план) |
| [1-lifecycle](1-lifecycle/) — ЖЦ і вимоги | [process](1-lifecycle/process.md) · [srs](1-lifecycle/srs.md) · [mvp](1-lifecycle/mvp.md) · [traceability](1-lifecycle/traceability.md) · [sprint-plan](1-lifecycle/sprint-plan.md) · [backlog](1-lifecycle/backlog.md) · [changes](1-lifecycle/changes.md) |
| [2-architecture](2-architecture/) — архітектура | [use-cases](2-architecture/use-cases.md) · [class-diagram](2-architecture/class-diagram.md) · [architecture](2-architecture/architecture.md) · [modules](2-architecture/modules.md) · [api](2-architecture/api.md) · [integration-plan](2-architecture/integration-plan.md) · [ADR](2-architecture/adr/) · [prototype](2-architecture/prototype/README.md) · [user-flow](2-architecture/user-flow.md) |
| [3-implementation](3-implementation/) — дані | [data-model](3-implementation/data-model.md) · [validation-rules](3-implementation/validation-rules.md) · [git-workflow](3-implementation/git-workflow.md) |
| [4-quality](4-quality/) — якість | [test-plan](4-quality/test-plan.md) · [test-cases](4-quality/test-cases.md) · [test-report](4-quality/test-report.md) · [bug-reports](4-quality/bug-reports.md) · [review-report](4-quality/review-report.md) · [acceptance.feature](4-quality/acceptance.feature) |
| [5-management](5-management/) — управління | [plan](5-management/plan.md) · [risks](5-management/risks.md) · [release-plan](5-management/release-plan.md) · [user-guide](5-management/user-guide.md) · [support](5-management/support.md) · [roadmap](5-management/roadmap.md) · [privacy](5-management/privacy.md) |
| Корінь | [CHANGELOG](CHANGELOG.md) · [LICENSE](LICENSE) · [docs.yml](.github/workflows/docs.yml) · [ci.yml](.github/workflows/ci.yml) |

## Запуск

Потрібні Python 3.12, Node 24 і безкоштовний ключ Gemini: <https://aistudio.google.com/apikey> → **Create API key** (картка не потрібна).

Бекенд:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows; на Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # вписати GEMINI_API_KEY
uvicorn app.main:app --reload   # http://localhost:8000/docs — OpenAPI
```

Фронтенд (другий термінал):

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173, /api проксіюється на :8000
```

Без ключа: `LLM_PROVIDER=mock` у `backend/.env` — заглушка без мережі.

Розгортання на сервері: `cp backend/.env.example backend/.env`, заповнити ключ і `CORS_ORIGINS`, потім `docker compose up -d --build` — сайт на порту 8080. Деталі — у [release-plan](5-management/release-plan.md).

## Тести

```bash
cd backend && pytest -q && ruff check .      # 28 тестів
cd frontend && npm test && npm run lint      # 5 тестів
```

Системне тестування — вручну, за чек-листом у [test-cases.md](4-quality/test-cases.md) (TC-28…TC-40), результати — у протоколі [test-report.md](4-quality/test-report.md); проводить Макс Сахошко. GitHub Actions: [ci.yml](.github/workflows/ci.yml) — код, [docs.yml](.github/workflows/docs.yml) — Markdown і посилання.

## Налаштування LLM

| Змінна в `backend/.env` | За замовчуванням | Опис |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` (безкоштовно) · `anthropic` (Claude, платно) · `mock` (заглушка) |
| `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` | — | ключ обраного провайдера |
| `LLM_MODEL` | `gemini-3.8-flash` / `claude-opus-5-5` | швидша модель: `gemini-3.5-flash-lite` (див. [ADR-0002](2-architecture/adr/0002-llm-provider-gemini.md)) |
| `LLM_TIMEOUT_S` | `15` | таймаут виклику LLM |
| `LLM_MAX_RETRIES` | `1` | повтори при збоях мережі / 5xx |
| `LLM_MAX_CONCURRENCY` | `20` | одночасних викликів LLM, далі 429 |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | домени фронтенду |

На безкоштовному тарифі Gemini є ліміти запитів, а Google може використовувати запити для покращення моделей — тож у застосунок вводимо лише імʼя ([privacy](5-management/privacy.md)).

## Ліцензія

[MIT](LICENSE). Використання також регулюється умовами обраного LLM-провайдера (Gemini API Additional Terms / Anthropic Usage Policy).
