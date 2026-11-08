from app.quality import review
from app.schemas import Style

GOOD = "Сашо, з днем народження! Бажаю щастя і натхнення. Нехай усе вдається."


def test_good_greeting_has_no_remarks():
    assert review(GOOD, "Саша", Style.warm) == []


def test_name_in_vocative_counts_as_mentioned():
    # «Сашо» — кличний відмінок від «Саша» (CR-04)
    assert "немає імені «Саша»" not in review(GOOD, "Саша", Style.warm)


def test_double_name_needs_both_parts():
    text = "Анно-Маріє, з днем народження! Бажаю щастя."
    assert review(text, "Анна-Марія", Style.warm) == []
    assert review("Анно, з днем народження! Бажаю щастя.", "Анна-Марія", Style.warm)


def test_missing_name():
    assert "немає імені «Саша»" in review("З днем народження! Бажаю щастя.", "Саша", Style.warm)


def test_sentence_count_bounds():
    assert "речень 1, а має бути 2–5" in review("Сашо, з днем народження!", "Саша", Style.warm)
    six = " ".join(["Сашо, вітаю!"] * 6)
    assert "речень 6, а має бути 2–5" in review(six, "Саша", Style.warm)


def test_english_text():
    text = "Happy birthday, Sasha! Wishing you joy."
    assert "текст не українською" in review(text, "Саша", Style.warm)


def test_official_without_emoji_and_slang():
    text = "Шановна Сашо, вітаємо! Ви справжня сігма 🎉."
    remarks = review(text, "Саша", Style.official)
    assert "емодзі в стилі «Офіційно»" in remarks
    assert "сленг у стилі «Офіційно»" in remarks
    # у брейнроті те саме — норма
    assert review(text, "Саша", Style.brainrot) == []


def test_last_sentence_ending_with_emoji_is_counted():
    text = "Сашо, вітаю! Бажаю щастя 🎉"  # дано: останнє речення без крапки, лише емодзі
    remarks = review(text, "Саша", Style.warm)  # дія
    assert remarks == []  # перевірка: 2 речення — у межах 2–5


def test_single_sentence_without_punctuation_is_one_not_zero():
    remarks = review("Сашо, з днем народження 🎉", "Саша", Style.warm)
    assert "речень 1, а має бути 2–5" in remarks


def test_typographic_apostrophe_in_text_matches_name():
    # BUG-13: користувач ввів «'», модель пише типографський «’»
    remarks = review("Мар’яно, вітаю! Бажаю щастя.", "Мар'яна", Style.warm)
    assert remarks == []


def test_sentence_boundaries_2_and_5_are_valid():
    two = "Сашо, вітаю! Бажаю щастя."
    five = "Сашо, вітаю! Бажаю щастя. Будь здоровий. Мрій сміливо. Обіймаю."
    assert review(two, "Саша", Style.warm) == []
    assert review(five, "Саша", Style.warm) == []
