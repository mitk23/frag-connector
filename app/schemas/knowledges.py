from typing import Any, Literal

from pydantic import BaseModel


class KnowledgeQueryRequestConfig(BaseModel):
    top_k: int | None = 3
    include_embedding: bool | None = True
    # include_metadata: bool | None = True
    filter: dict[str, Any] | None = None


class KnowledgeQueryRequest(BaseModel):
    embedding: list[float]
    config: KnowledgeQueryRequestConfig


class KnowledgeResponse(BaseModel):
    id: str | None = None
    text: str | None = None
    embedding: list[float] | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None


class FederatedKnowledgeQueryRequest(BaseModel):
    query: KnowledgeQueryRequest
    providers: list[str] | None = None
    include_provider_contribution: bool = False
    knowledge_rerank_method: Literal["naive", "cosine"] | None = "naive"
