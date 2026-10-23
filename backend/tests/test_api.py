import asyncio

import pytest
from fastapi.testclient import TestClient

from app.llm import PROVIDER_BUSY_MESSAGE, LLMBusy, LLMUnavailable, MockGenerator
from app.main import create_app
from app.prompts import build_user_prompt
from app.schemas import Style


class FailingGenerator:
    async def generate(self, name, style):
        raise LLMUnavailable("Сервіс генерації тимчасово недоступний")


@pytest.fixture
def client():
    return TestClient(create_app(MockGenerator()))


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_generate_greeting(client):
    r = client.post("/api/greetings", json={"name": "Саша", "style": "brainrot"})
    assert r.status_code == 200
    body = r.json()
    assert "Саша" in body["text"]
    assert body["style"] == "brainrot"


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "style": "warm"},
        {"name": "   ", "style": "warm"},
        {"name": "Саша", "style": "unknown"},
        {"name": "x" * 51, "style": "warm"},
        {"style": "warm"},
    ],
)
def test_validation(client, payload):
    assert client.post("/api/greetings", json=payload).status_code == 422


def test_name_is_trimmed(client):
    r = client.post("/api/greetings", json={"name": "  Саша  ", "style": "warm"})
    assert r.status_code == 200
    assert "Саша!" in r.json()["text"]


@pytest.mark.parametrize("length,status", [(1, 200), (50, 200), (51, 422)])
def test_name_length_boundaries(client, length, status):
    r = client.post("/api/greetings", json={"name": "я" * length, "style": "warm"})
    assert r.status_code == status


def test_provider_limit_returns_429_with_minute_hint():
    class BusyGenerator:
        async def generate(self, name, style):
            raise LLMBusy(PROVIDER_BUSY_MESSAGE)

    r = TestClient(create_app(BusyGenerator())).post(
        "/api/greetings", json={"name": "Саша", "style": "warm"}
    )
    assert r.status_code == 429
    assert "хвилину" in r.json()["detail"]


def test_llm_unavailable_returns_503():
    client = TestClient(create_app(FailingGenerator()))
    r = client.post("/api/greetings", json={"name": "Саша", "style": "warm"})
    assert r.status_code == 503
    assert r.json()["detail"]


def test_concurrency_limit_returns_429():
    app = create_app(MockGenerator())
    app.state.llm_slots = asyncio.Semaphore(0)  # усі слоти зайняті
    r = TestClient(app).post("/api/greetings", json={"name": "Саша", "style": "warm"})
    assert r.status_code == 429


def test_cors_rejects_foreign_origin(client):
    r = client.options(
        "/api/greetings",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in r.headers


@pytest.mark.parametrize("style", list(Style))
def test_prompt_contains_name_and_style(style):
    prompt = build_user_prompt("  Саша ", style)
    assert "Саша" in prompt
    assert "  Саша " not in prompt
