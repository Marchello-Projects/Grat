"""Консольний інкремент ДРбота: імʼя → стиль → привітання, без інтерфейсу.

Запуск із теки backend/:
    python -m app.cli Саша --style warm

Спільний шар запуску: лише склеює модулі names (Аліна), llm (Марк) і quality (Макс).
"""

import argparse
import asyncio
import sys

from . import names, quality
from .config import settings
from .llm import LLMBusy, LLMUnavailable, make_generator
from .schemas import Style


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # кирилиця й емодзі в консолі Windows
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="drbot", description="Привітання з днем народження")
    parser.add_argument("name", help="імʼя іменинника")
    parser.add_argument("--style", choices=[s.value for s in Style], default=Style.warm.value)
    args = parser.parse_args(argv)

    name, reason = names.check(args.name)
    if reason:
        print(reason, file=sys.stderr)
        return 2

    style = Style(args.style)
    try:
        text = asyncio.run(make_generator(settings).generate(name, style))
    except (LLMBusy, LLMUnavailable) as e:
        print(e, file=sys.stderr)
        return 1

    print(text, flush=True)  # інакше зауваження з stderr зʼявляються вище за привітання
    for remark in quality.review(text, name, style):
        print(f"⚠ {remark}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
