import asyncio
from types import SimpleNamespace

import pytest
from google.genai import errors as genai_errors

from app.config import Settings
from app.llm import GeminiGenerator, LLMBusy, LLMUnavailable, make_generator
from app.schemas import Style


class FakeModels:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def make_gemini(result=None, error=None):
    models = FakeModels(result, error)
    client = SimpleNamespace(aio=SimpleNamespace(models=models))
    return GeminiGenerator(Settings(llm_provider="gemini", _env_file=None), client), models


def api_error(code: int) -> genai_errors.APIError:
    return genai_errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X"}})


def run(coro):
    return asyncio.run(coro)


def test_returns_text_and_sends_prompt():
    response = SimpleNamespace(text="  Вітаю, Саша!  ", usage_metadata=None)
    gen, models = make_gemini(result=response)
    assert run(gen.generate("Саша", Style.warm)) == "Вітаю, Саша!"
    call = models.calls[0]
    assert call["model"] == "gemini-3.8-flash"
    assert "Саша" in call["contents"]
    assert call["config"].system_instruction


def test_rate_limit_maps_to_busy():
    gen, _ = make_gemini(error=api_error(429))
    with pytest.raises(LLMBusy):
        run(gen.generate("Саша", Style.warm))


@pytest.mark.parametrize("code", [400, 403, 500, 503])
def test_api_errors_map_to_unavailable(code):
    gen, _ = make_gemini(error=api_error(code))
    with pytest.raises(LLMUnavailable):
        run(gen.generate("Саша", Style.warm))


def test_network_error_maps_to_unavailable():
    gen, _ = make_gemini(error=TimeoutError())
    with pytest.raises(LLMUnavailable):
        run(gen.generate("Саша", Style.warm))


def test_blocked_response_maps_to_unavailable():
    gen, _ = make_gemini(result=SimpleNamespace(text=None, usage_metadata=None))
    with pytest.raises(LLMUnavailable):
        run(gen.generate("Саша", Style.warm))


def test_missing_key_gives_clear_error():
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        make_generator(Settings(llm_provider="gemini", gemini_api_key="", _env_file=None))


def test_unknown_provider():
    with pytest.raises(ValueError):
        make_generator(Settings(llm_provider="openai", _env_file=None))
