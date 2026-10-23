# Діаграма класів предметної області

Імена класів англійською — як у коді; пояснення українською в таблиці нижче. Класи з позначкою «v0.2+» ще не реалізовані.

```mermaid
classDiagram
    direction LR

    class GreetingRequest {
        +str name
        +Style style
        +list~Interest~ interests
        +Length length
        +Harshness harshness
        +datetime created_at
        +validate() bool
    }

    class Style {
        <<enumeration>>
        BRAINROT
        WARM
        OFFICIAL
        +hint() str
    }

    class Interest {
        +int id
        +str title
        +bool is_custom
    }

    class Greeting {
        +UUID id
        +str text
        +str model
        +int input_tokens
        +int output_tokens
        +float latency_s
        +render() str
    }

    class Rating {
        +UUID greeting_id
        +RatingValue value
        +datetime created_at
        +change(value) void
    }

    class GreetingCard {
        +str slug
        +datetime expires_at
        +url() str
    }

    class PromptBuilder {
        +str system_prompt
        +build(request) str
    }

    class GreetingGenerator {
        <<interface>>
        +generate(name, style) str
    }

    class GeminiGenerator {
        -str model
        -Client client
        +generate(name, style) str
    }

    class ClaudeGenerator {
        -str model
        +generate(name, style) str
    }

    class MockGenerator {
        +generate(name, style) str
    }

    class DailyUsage {
        +date day
        +int generations
        +int tokens
        +is_over_limit() bool
    }

    GreetingRequest "1" --> "1" Style
    GreetingRequest "1" o-- "0..3" Interest
    GreetingRequest "1" --> "1..*" Greeting : породжує
    Greeting "1" --> "0..1" Rating
    Greeting "1" --> "0..1" GreetingCard
    PromptBuilder ..> GreetingRequest : читає
    GreetingGenerator ..> PromptBuilder : використовує
    GreetingGenerator <|.. GeminiGenerator
    GreetingGenerator <|.. ClaudeGenerator
    GreetingGenerator <|.. MockGenerator
    GreetingGenerator ..> Greeting : створює
    DailyUsage ..> Greeting : рахує
```

| Клас | Що означає | Реалізовано |
|---|---|---|
| `GreetingRequest` | Запит на привітання: імʼя, стиль, інтереси, налаштування | частково: `name`, `style` (`backend/app/schemas.py`) |
| `Style` | Стиль гумору з інструкцією для LLM | ✅ `Style`, `STYLE_HINTS` |
| `Interest` | Інтерес іменинника зі списку або власний | v0.2 |
| `Greeting` | Згенерований текст і метадані виклику | частково: `GreetingResponse` (`text`, `style`) |
| `Rating` | Оцінка 👍/👎 | v0.3 |
| `GreetingCard` | Сторінка-листівка з коротким посиланням | Won't (після v1.0) |
| `PromptBuilder` | Збирає промпт із правилами безпеки й стилем | ✅ `build_user_prompt`, `SYSTEM_PROMPT` |
| `GreetingGenerator` | Інтерфейс генератора: один метод `generate` | ✅ `Protocol` у `backend/app/llm.py` |
| `GeminiGenerator`, `ClaudeGenerator`, `MockGenerator` | Реалізації для Gemini, Claude і заглушки | ✅ |
| `DailyUsage` | Лічильник генерацій і токенів на добу (NFR-2) | v0.3 |

Звʼязки: запит породжує одне або кілька привітань (кожна перегенерація — нове), привітання може мати одну оцінку й одну листівку. Генератор залежить від інтерфейсу, а не від конкретного провайдера — це забезпечує NFR-9.
