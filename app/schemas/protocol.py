from typing import Any, TypeAlias

from pydantic import BaseModel


class RetrieveRequest(BaseModel):
    query_vector: list[float]
    top_k: int = 3
    include_vector: bool = False


class RetrieveResponseElement(BaseModel):
    id: str
    score: float
    text: str | None = None
    metadata: dict[str, Any] | None = None
    vector: list[float] | None = None


RetrieveResponse: TypeAlias = list[RetrieveResponseElement]


class GenerateRequest(BaseModel):
    model: str
    user_prompt: str
    system_prompt: str | None = None


class GenerateResponse(BaseModel):
    answer: str
