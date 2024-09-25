from typing import Literal

from pydantic import BaseModel


class MessageToLLM(BaseModel):
    content: str
    role: Literal["user", "system"] | None = "user"


class QuestionOllamaDao(BaseModel):
    model: str
    messages: list[MessageToLLM]
    stream: bool | None = True
