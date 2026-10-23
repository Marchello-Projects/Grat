from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, StringConstraints


class Style(StrEnum):
    brainrot = "brainrot"
    warm = "warm"
    official = "official"


# пробіли по краях обрізаються до перевірки довжини: імʼя "   " невалідне
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class GreetingRequest(BaseModel):
    name: Name
    style: Style


class GreetingResponse(BaseModel):
    text: str
    style: Style


class ErrorResponse(BaseModel):
    detail: str
