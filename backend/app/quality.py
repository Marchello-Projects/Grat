"""Модуль quality (Макс): перевірка властивостей привітання.

Текст моделі щоразу інший, тож перевіряємо не збіг, а властивості (TC-48…TC-51).
"""

import re

from .schemas import Style

EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")
SENTENCE_END = re.compile(r"[.!?…]+(?=\s|$)")
LATIN = re.compile(r"[A-Za-z]")
CYRILLIC = re.compile(r"[А-Яа-яЄєІіЇїҐґ]")
SLANG = ("скібіді", "сігма", "різз", "аура")


APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "`": "'"})


def _mentions(text: str, name: str) -> bool:
    """Імʼя в будь-якому відмінку: «Саша», «Сашо», «Саше» мають спільну основу «Саш»."""
    # «Мар'яна» від користувача і «Мар’яно» від моделі — той самий апостроф (BUG-13)
    lowered = text.lower().translate(APOSTROPHES)
    for part in re.split(r"[\s-]+", name.lower().translate(APOSTROPHES)):
        stem = part if len(part) <= 3 else part[:-1]
        if stem not in lowered:
            return False
    return True


def _count_sentences(text: str) -> int:
    """Речення закінчується «.!?…»; хвіст із літерами без крапки (… щастя 🎉) — теж речення."""
    ends = list(SENTENCE_END.finditer(text))
    tail = text[ends[-1].end():] if ends else text
    return len(ends) + (1 if re.search(r"\w", tail) else 0)


def review(text: str, name: str, style: Style) -> list[str]:
    """Повертає список зауважень до привітання; порожній — зауважень немає."""
    remarks = []
    if not _mentions(text, name):
        remarks.append(f"немає імені «{name}»")
    sentences = _count_sentences(text)
    if not 2 <= sentences <= 5:
        remarks.append(f"речень {sentences}, а має бути 2–5")
    latin, cyrillic = len(LATIN.findall(text)), len(CYRILLIC.findall(text))
    if latin > cyrillic:
        remarks.append("текст не українською")
    if style is Style.official:
        if EMOJI.search(text):
            remarks.append("емодзі в стилі «Офіційно»")
        if any(word in text.lower() for word in SLANG):
            remarks.append("сленг у стилі «Офіційно»")
    return remarks
