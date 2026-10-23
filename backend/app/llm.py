import asyncio
import logging
import random
import time
from typing import Protocol

import anthropic
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from .config import Settings
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import Style

log = logging.getLogger("drbot.llm")

# ліміт провайдера може бути добовим, тож «кілька секунд» тут вводило б в оману
PROVIDER_BUSY_MESSAGE = "Сервіс генерації зараз перевантажений, спробуйте за хвилину"


class LLMUnavailable(Exception):
    """Провайдер недоступний або не зміг дати відповідь → 503."""


class LLMBusy(Exception):
    """Перевищено ліміт одночасних викликів або ліміт провайдера → 429."""


class GreetingGenerator(Protocol):
    async def generate(self, name: str, style: Style) -> str: ...


def _log_success(provider: str, model: str, style: Style, started: float, **usage) -> None:
    details = " ".join(f"{k}={v}" for k, v in usage.items())
    log.info(
        "greeting generated provider=%s model=%s style=%s %s %.2fs",
        provider,
        model,
        style.value,
        details,
        time.perf_counter() - started,
    )


class GeminiGenerator:
    """Google Gemini API: безкоштовний тариф із ключем з Google AI Studio."""

    def __init__(self, settings: Settings, client: genai.Client | None = None):
        if client is None and not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY не задано. Отримайте безкоштовний ключ на "
                "https://aistudio.google.com/apikey і впишіть його в backend/.env "
                "(або поставте LLM_PROVIDER=mock)."
            )
        self._model = settings.model
        self._client = client or genai.Client(
            api_key=settings.gemini_api_key,
            http_options=genai_types.HttpOptions(
                timeout=int(settings.llm_timeout_s * 1000),  # мілісекунди
                retry_options=genai_types.HttpRetryOptions(
                    attempts=settings.llm_max_retries + 1,
                    http_status_codes=[500, 502, 503, 504],
                ),
            ),
        )
        self._config = genai_types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            thinking_config=genai_types.ThinkingConfig(thinking_level="low"),
            max_output_tokens=2000,
        )

    async def generate(self, name: str, style: Style) -> str:
        started = time.perf_counter()
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=build_user_prompt(name, style),
                config=self._config,
            )
        except genai_errors.APIError as e:
            if e.code == 429:
                raise LLMBusy(PROVIDER_BUSY_MESSAGE) from e
            log.warning("Gemini call failed: %s %s", e.code, e.message)
            raise LLMUnavailable("Сервіс генерації тимчасово недоступний") from e
        except Exception as e:  # мережа, таймаут
            log.warning("Gemini call failed: %r", e)
            raise LLMUnavailable("Сервіс генерації тимчасово недоступний") from e

        # text == None, якщо відповідь заблокував фільтр безпеки Gemini
        text = (response.text or "").strip()
        if not text:
            raise LLMUnavailable("Не вдалося згенерувати привітання, спробуйте ще раз")

        usage = response.usage_metadata
        _log_success(
            "gemini",
            self._model,
            style,
            started,
            in_tokens=usage.prompt_token_count if usage else None,
            out_tokens=usage.candidates_token_count if usage else None,
            # токени «обдумування» оплачуються як вихідні, без них оцінка вартості занижена
            thinking_tokens=usage.thoughts_token_count if usage else None,
        )
        return text


class ClaudeGenerator:
    """Anthropic Claude API (платний)."""

    def __init__(self, settings: Settings):
        self._model = settings.model
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or None,
            timeout=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )

    async def generate(self, name: str, style: Style) -> str:
        started = time.perf_counter()
        try:
            response = await self._client.beta.messages.create(
                model=self._model,
                max_tokens=2000,
                output_config={"effort": "low"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_user_prompt(name, style)}],
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError as e:
            raise LLMBusy(PROVIDER_BUSY_MESSAGE) from e
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
            log.warning("Claude call failed: %r", e)
            raise LLMUnavailable("Сервіс генерації тимчасово недоступний") from e

        if response.stop_reason == "refusal":
            raise LLMUnavailable("Не вдалося згенерувати привітання, спробуйте ще раз")

        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if not text:
            raise LLMUnavailable("Не вдалося згенерувати привітання, спробуйте ще раз")

        _log_success(
            "anthropic",
            response.model,
            style,
            started,
            in_tokens=response.usage.input_tokens,
            out_tokens=response.usage.output_tokens,
        )
        return text


class MockGenerator:
    """Заглушка: відповідає без мережі. delay — імітація часу генерації LLM."""

    def __init__(self, delay: tuple[float, float] = (0.0, 0.0)):
        self._delay = delay

    async def generate(self, name: str, style: Style) -> str:
        await asyncio.sleep(random.uniform(*self._delay))
        return f"[{style.value}] З днем народження, {name}! 🎉"


def make_generator(settings: Settings) -> GreetingGenerator:
    match settings.llm_provider:
        case "mock":
            return MockGenerator(delay=(0.5, 1.5))
        case "gemini":
            return GeminiGenerator(settings)
        case "anthropic":
            return ClaudeGenerator(settings)
        case other:
            raise ValueError(f"Невідомий LLM_PROVIDER={other!r}: gemini | anthropic | mock")
