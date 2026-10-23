# Системні тести в браузері

Сценарій [system_tests.py](system_tests.py) проходить системні кейси TC-28…TC-40 ([test-cases.md](../test-cases.md)) у Microsoft Edge і знімає скриншоти для [prototype/](../../2-architecture/prototype/README.md).

## Запуск

1. Запустіть бекенд (з `GEMINI_API_KEY`) і фронтенд, як у [README](../../README.md#запуск).
2. В окремому віртуальному середовищі:

   ```bash
   python -m venv .venv-e2e
   .venv-e2e/Scripts/pip install playwright
   .venv-e2e/Scripts/python 4-quality/system-tests/system_tests.py 2-architecture/prototype results.json
   ```

   Браузер не завантажується: використовується встановлений Edge (`channel="msedge"`). Для Chrome замініть канал на `chrome`.

3. Результати — у `results.json`; збережіть копію як `results-<дата>.json` і оновіть [test-report.md](../test-report.md).

Помилки 429, 503 і обрив мережі моделюються підміною відповіді сервера (`page.route`), тож для них Gemini не викликається. Кейси TC-32…TC-34 і TC-40 викликають реальний Gemini — це 4 запити безкоштовного тарифу на прогін.
