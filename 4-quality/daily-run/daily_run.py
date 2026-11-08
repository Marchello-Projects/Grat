"""Щоранковий прогін ДРбота: запити до запущеного бекенду й зведення за день.

Запуск (бекенд уже працює):
    python daily_run.py                       # http://127.0.0.1:8000
    python daily_run.py --url http://IP:8000 --per-style 3 --users 5

Що робить:
  1. health        — GET /api/health
  2. генерації     — по --per-style запитів на кожен стиль, послідовно, як один користувач
  3. одночасні     — --users запитів одночасно, як кілька людей на сервері
Результат — таблиця в консолі й рядок у results.jsonl поруч зі скриптом.
Лише стандартна бібліотека Python, нічого встановлювати не треба.
"""

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

STYLES = ["brainrot", "warm", "official"]
LIMIT_S = 10.0  # NFR-1
RESULTS = Path(__file__).with_name("results.jsonl")


def request(url: str, body: dict | None = None, timeout: float = 60) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, payload = r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        status, payload = e.code, json.loads(e.read() or b"{}")
    except OSError as e:  # сервер не запущений, таймаут
        status, payload = 0, {"detail": repr(e)}
    return {"status": status, "time_s": round(time.perf_counter() - started, 1), **payload}


def generate(base: str, style: str) -> dict:
    r = request(f"{base}/api/greetings", {"name": "Саша", "style": style})
    r["style"] = style
    return r


def summary(results: list[dict]) -> dict:
    ok = [r for r in results if r["status"] == 200]
    times = [r["time_s"] for r in ok]
    codes: dict[str, int] = {}
    for r in results:
        codes[str(r["status"])] = codes.get(str(r["status"]), 0) + 1
    return {
        "total": len(results),
        "ok": len(ok),
        "codes": codes,
        "median_s": statistics.median(times) if times else None,
        "max_s": max(times) if times else None,
        "over_10s": sum(t > LIMIT_S for t in times),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--per-style", type=int, default=3)
    p.add_argument("--users", type=int, default=5)
    args = p.parse_args()

    health = request(f"{args.url}/api/health", timeout=5)
    print(f"health: {health['status']}")
    if health.get("status") != "ok":
        # на порту не ДРбот (інший сервер) або бекенд не запущено — у протокол не пишемо
        raise SystemExit(f"Бекенд ДРбота не відповідає на {args.url}/api/health: {health}")

    sequential = [generate(args.url, s) for s in STYLES for _ in range(args.per_style)]
    with ThreadPoolExecutor(args.users) as pool:
        concurrent = list(pool.map(lambda s: generate(args.url, s), [STYLES[i % 3] for i in range(args.users)]))

    for title, rows in (("Генерації по черзі", sequential), (f"{args.users} одночасних", concurrent)):
        print(f"\n{title}:")
        for r in rows:
            note = r.get("text", r.get("detail", ""))[:70].replace("\n", " ")
            print(f"  {r['style']:<9} {r['status']:>3} {r['time_s']:>5} с  {note}")
        print(f"  → {summary(rows)}")

    record = {
        "date": datetime.now().isoformat(timespec="minutes"),
        "health": health["status"],
        "sequential": summary(sequential),
        "concurrent": summary(concurrent),
        "errors": sorted({r.get("detail", "") for r in sequential + concurrent if r["status"] != 200}),
    }
    with RESULTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\nЗаписано в {RESULTS.name}")


if __name__ == "__main__":
    main()
