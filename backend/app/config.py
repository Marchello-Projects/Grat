from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "anthropic": "claude-opus-5-5",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # gemini — безкоштовний тариф Google AI Studio
    # anthropic — платний Claude API
    # mock — заглушка без мережі (розробка, тести, навантажувальний тест)
    llm_provider: str = "gemini"
    # порожньо → модель за замовчуванням для обраного провайдера
    llm_model: str = ""
    # резерв через кому, по черзі: «gemini:gemini-3.5-flash-lite,templates» (ADR-0005)
    llm_fallbacks: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    llm_timeout_s: float = 15.0
    llm_max_retries: int = 1
    llm_max_concurrency: int = 20
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def model(self) -> str:
        return self.llm_model or DEFAULT_MODELS.get(self.llm_provider, "")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
