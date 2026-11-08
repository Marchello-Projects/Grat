"""Модуль names (Аліна): чи є введений текст імʼям.

Імʼя потрапляє в промпт моделі, тож усе, що схоже на інструкцію, відхиляємо (BUG-11).
"""

import unicodedata

MAX_LENGTH = 50
MAX_WORDS = 3
# в імені бувають апостроф і дефіс; решта розділових знаків робить «імʼя» командою для ШІ
ALLOWED_PUNCTUATION = {"'", "’", "-", "‐"}


def _is_forbidden(char: str) -> bool:
    """Будь-який розділовий знак Unicode (не лише ASCII «.»), цифра чи службовий символ."""
    if char in ALLOWED_PUNCTUATION:
        return False
    category = unicodedata.category(char)
    # P* — пунктуація («…», «。», «．» теж), N* — цифри, Sm/Sc/Sk — +, $, ` тощо.
    # So (емодзі) дозволено: «Саша 🎉» — валідне імʼя.
    return category[0] in "PN" or category in ("Sm", "Sc", "Sk")


def check(text: str) -> tuple[str, str | None]:
    """Повертає (імʼя, None) або ("", причина відмови українською)."""
    if "\n" in text or "\r" in text:
        return "", "Введіть лише імʼя — в один рядок"
    name = " ".join(text.split())  # обрізає краї й зайві пробіли всередині
    # на українській розкладці апостроф часто набирають клавішею ` (BUG-12)
    name = name.replace("`", "'")
    if not name:
        return "", "Введіть імʼя іменинника"
    if len(name) > MAX_LENGTH:
        return "", f"Імʼя задовге: до {MAX_LENGTH} символів"
    if any(_is_forbidden(char) for char in name):
        return "", "Введіть лише імʼя — без розділових знаків і пояснень"
    if len(name.split()) > MAX_WORDS:
        return "", f"Введіть лише імʼя — до {MAX_WORDS} слів"
    return name, None
