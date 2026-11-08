import asyncio

import pytest

from app.config import Settings
from app.llm import (
    TEMPLATES,
    FallbackGenerator,
    LLMBusy,
    LLMUnavailable,
    TemplateGenerator,
    make_generator,
)
from app.quality import review
from app.schemas import Style


class Fake:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, 0

    async def generate(self, name, style):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def test_first_answer_wins_and_rest_not_called():
    first, second = Fake("перше"), Fake("друге")
    gen = FallbackGenerator([("a", first), ("b", second)])
    assert asyncio.run(gen.generate("Саша", Style.warm)) == "перше"
    assert second.calls == 0


@pytest.mark.parametrize("error", [LLMUnavailable("504"), LLMBusy("429")])
def test_falls_back_on_unavailable_and_busy(error):
    gen = FallbackGenerator([("main", Fake(error=error)), ("reserve", Fake("резерв"))])
    assert asyncio.run(gen.generate("Саша", Style.warm)) == "резерв"


def test_all_failed_raises_last_error():
    chain = [("a", Fake(error=LLMUnavailable("a"))), ("b", Fake(error=LLMBusy("b")))]
    gen = FallbackGenerator(chain)
    with pytest.raises(LLMBusy):
        asyncio.run(gen.generate("Саша", Style.warm))


def test_make_generator_builds_chain_from_settings():
    settings = Settings(llm_provider="mock", llm_fallbacks="templates", _env_file=None)
    assert isinstance(make_generator(settings), FallbackGenerator)


@pytest.mark.parametrize("style", list(Style))
def test_templates_pass_quality_checks(style):
    # стик llm ↔ quality: остання ланка резерву має проходити ті самі перевірки, що й модель
    for template in TEMPLATES[style]:
        text = template.format(name="Саша")
        assert review(text, "Саша", style) == [], text


def test_template_generator_inserts_name():
    text = asyncio.run(TemplateGenerator().generate("Мар'яна", Style.official))
    assert text.startswith("Мар'яна,")


def test_unexpected_error_in_link_falls_back_too():
    # дано: адаптер упав не «нашою» помилкою, а несподіваною (баг SDK, зламана відповідь)
    gen = FallbackGenerator([("main", Fake(error=RuntimeError("boom"))), ("t", Fake("шаблон"))])
    text = asyncio.run(gen.generate("Саша", Style.warm))  # дія
    assert text == "шаблон"  # перевірка: користувач однаково отримав привітання


@pytest.mark.parametrize("fallbacks", ["templates,", "templates,,mock"])
def test_fallbacks_tolerate_trailing_comma_and_spaces(fallbacks):
    # BUG-14: зайва кома чи пробіли в .env не мають валити сервер на старті
    settings = Settings(llm_provider="mock", llm_fallbacks=fallbacks, _env_file=None)
    assert isinstance(make_generator(settings), FallbackGenerator)
