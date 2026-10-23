import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .llm import GreetingGenerator, LLMBusy, LLMUnavailable, make_generator
from .schemas import ErrorResponse, GreetingRequest, GreetingResponse

logging.basicConfig(level=logging.INFO)


def create_app(generator: GreetingGenerator | None = None) -> FastAPI:
    app = FastAPI(title="ДРбот API", version="0.1.0")
    app.state.generator = generator or make_generator(settings)
    # Глобальне обмеження одночасних викликів LLM (розділ 7): надлишок отримує 429
    app.state.llm_slots = asyncio.Semaphore(settings.llm_max_concurrency)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post(
        "/api/greetings",
        response_model=GreetingResponse,
        responses={429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    async def create_greeting(body: GreetingRequest, request: Request) -> GreetingResponse:
        slots: asyncio.Semaphore = request.app.state.llm_slots
        if slots.locked():
            raise HTTPException(429, "Забагато запитів, зачекайте кілька секунд")
        async with slots:
            try:
                text = await request.app.state.generator.generate(body.name, body.style)
            except LLMBusy as e:
                raise HTTPException(429, str(e))
            except LLMUnavailable as e:
                raise HTTPException(503, str(e))
        return GreetingResponse(text=text, style=body.style)

    return app


app = create_app()
