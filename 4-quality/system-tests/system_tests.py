"""Системні кейси ST-xx на запущеному прототипі + скриншоти для prototype/.

Usage: python system_tests.py <out_dir_for_png> <results.json>
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

URL = "http://localhost:5173"
OUT = Path(sys.argv[1])
RESULTS = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
results = []


def case(case_id, title):
    def deco(fn):
        def run(page):
            started = time.perf_counter()
            try:
                note = fn(page) or ""
                status = "PASS"
            except Exception as e:  # noqa: BLE001
                status, note = "FAIL", f"{type(e).__name__}: {str(e)[:200]}"
            results.append(
                {"id": case_id, "title": title, "status": status, "note": note,
                 "seconds": round(time.perf_counter() - started, 2)}
            )
            print(case_id, status, note)

        return run

    return deco


def fresh(page):
    page.unroute("**/api/greetings")
    page.goto(URL)
    page.wait_for_selector("#name")


def fill_and_pick(page, name="Саша", style="Душевно"):
    page.fill("#name", name)
    page.get_by_role("button", name=style).click()


def mock_api(page, status, body, delay_ms=0):
    def handler(route):
        if delay_ms:
            time.sleep(delay_ms / 1000)
        route.fulfill(status=status, content_type="application/json", body=json.dumps(body))

    page.route("**/api/greetings", handler)


@case("ST-01", "Порожній стан: поле імені, без стилів і кнопки генерації")
def st01(page):
    fresh(page)
    expect(page.get_by_label("Імʼя іменинника")).to_be_visible()
    expect(page.get_by_role("button", name="Згенерувати")).to_have_count(0)
    expect(page.get_by_role("button", name="Брейнрот")).to_have_count(0)
    page.screenshot(path=OUT / "01-empty.png", full_page=True)


@case("ST-02", "Після введення імені зʼявляються 3 стилі, «Згенерувати» неактивна")
def st02(page):
    fresh(page)
    page.fill("#name", "Саша")
    for s in ("Брейнрот", "Душевно", "Офіційно"):
        expect(page.get_by_role("button", name=s)).to_be_visible()
    expect(page.get_by_role("button", name="Згенерувати")).to_be_disabled()
    page.screenshot(path=OUT / "02-name-entered.png", full_page=True)
    page.get_by_role("button", name="Брейнрот").click()
    expect(page.get_by_role("button", name="Згенерувати")).to_be_enabled()
    page.screenshot(path=OUT / "03-style-selected.png", full_page=True)


@case("ST-03", "Імʼя з одних пробілів не показує стилі")
def st03(page):
    fresh(page)
    page.fill("#name", "    ")
    expect(page.get_by_role("button", name="Брейнрот")).to_have_count(0)


@case("ST-04", "Під час генерації кнопка показує «Генеруємо…» і неактивна")
def st04(page):
    fresh(page)
    mock_api(page, 200, {"text": "Вітаю, Саша!", "style": "warm"}, delay_ms=1500)
    fill_and_pick(page)
    page.get_by_role("button", name="Згенерувати").click()
    btn = page.get_by_role("button", name="Генеруємо…")
    expect(btn).to_be_disabled()
    page.screenshot(path=OUT / "04-loading.png", full_page=True)
    expect(page.get_by_text("Вітаю, Саша!")).to_be_visible(timeout=5000)


def real_generation(page, style, shot=None):
    fresh(page)
    fill_and_pick(page, "Саша", style)
    started = time.perf_counter()
    page.get_by_role("button", name="Згенерувати").click()
    result = page.locator(".result p")
    expect(result).to_be_visible(timeout=10_000)  # NFR: ≤ 10 с
    elapsed = time.perf_counter() - started
    text = result.inner_text()
    # імʼя може стояти в кличному відмінку («Сашо»), тож перевіряємо основу
    assert "Саш" in text, f"імені немає в тексті: {text[:80]}"
    if shot:
        page.screenshot(path=OUT / shot, full_page=True)
    return f"{elapsed:.1f} с; «{text[:70]}…»"


@case("ST-05", "Реальна генерація (Gemini), стиль «Брейнрот»: текст з імʼям ≤ 10 с")
def st05(page):
    return real_generation(page, "Брейнрот", "05-result.png")


@case("ST-06", "Реальна генерація, стиль «Душевно»")
def st06(page):
    return real_generation(page, "Душевно")


@case("ST-07", "Реальна генерація, стиль «Офіційно»")
def st07(page):
    return real_generation(page, "Офіційно")


@case("ST-08", "API повертає 503 → повідомлення й кнопка «Повторити»")
def st08(page):
    fresh(page)
    mock_api(page, 503, {"detail": "Сервіс генерації тимчасово недоступний"})
    fill_and_pick(page)
    page.get_by_role("button", name="Згенерувати").click()
    expect(page.get_by_role("alert")).to_contain_text("тимчасово недоступний")
    expect(page.get_by_role("button", name="Повторити")).to_be_visible()
    page.screenshot(path=OUT / "06-error-503.png", full_page=True)


@case("ST-09", "«Повторити» після 503 повторює запит і показує привітання")
def st09(page):
    fresh(page)
    mock_api(page, 503, {"detail": "Сервіс генерації тимчасово недоступний"})
    fill_and_pick(page)
    page.get_by_role("button", name="Згенерувати").click()
    expect(page.get_by_role("alert")).to_be_visible()
    page.unroute("**/api/greetings")
    mock_api(page, 200, {"text": "Друга спроба вдалася, Саша!", "style": "warm"})
    page.get_by_role("button", name="Повторити").click()
    expect(page.get_by_text("Друга спроба вдалася, Саша!")).to_be_visible()
    expect(page.get_by_role("alert")).to_have_count(0)


@case("ST-10", "API повертає 429 → повідомлення «зачекайте»")
def st10(page):
    fresh(page)
    mock_api(page, 429, {"detail": "Забагато запитів, зачекайте кілька секунд"})
    fill_and_pick(page)
    page.get_by_role("button", name="Згенерувати").click()
    expect(page.get_by_role("alert")).to_contain_text("зачекайте")
    page.screenshot(path=OUT / "07-error-429.png", full_page=True)


@case("ST-11", "Немає мережі → повідомлення про звʼязок, без білого екрана")
def st11(page):
    fresh(page)
    page.route("**/api/greetings", lambda route: route.abort())
    fill_and_pick(page)
    page.get_by_role("button", name="Згенерувати").click()
    expect(page.get_by_role("alert")).to_contain_text("Немає звʼязку")
    page.screenshot(path=OUT / "08-error-network.png", full_page=True)


@case("ST-12", "Поле імені обмежене 50 символами")
def st12(page):
    fresh(page)
    page.fill("#name", "я" * 60)
    value = page.input_value("#name")
    assert len(value) == 50, len(value)


@case("ST-13", "Екран 360 px: немає горизонтальної прокрутки, привітання видно")
def st13(page):
    page.set_viewport_size({"width": 360, "height": 740})
    note = real_generation(page, "Душевно", "09-mobile-result.png")
    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    assert not overflow, "є горизонтальна прокрутка"
    fresh(page)
    page.screenshot(path=OUT / "10-mobile-empty.png", full_page=True)
    page.set_viewport_size({"width": 900, "height": 900})
    return note


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 900, "height": 900}, locale="uk-UA")
    for test in (st01, st02, st03, st04, st05, st06, st07, st08, st09, st10, st11, st12, st13):
        test(page)
    version = browser.version
    browser.close()

RESULTS.write_text(
    json.dumps({"browser": f"Microsoft Edge {version}", "results": results}, ensure_ascii=False,
               indent=2),
    encoding="utf-8",
)
