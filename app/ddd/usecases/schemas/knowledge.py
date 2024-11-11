from typing import Any

from ddd.domains.connector import ConnectorId
from ddd.domains.knowledge import (
    FederatedKnowledgeQuery,
    Knowledge,
    KnowledgeQuery,
    KnowledgeQueryConfig,
    KnowledgeRerankMethod,
)
from pydantic import BaseModel


class KnowledgeDto(BaseModel):
    id: str | None = None
    text: str | None = None
    embedding: list[float] | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None

    def to_entity(self) -> Knowledge:
        return Knowledge(id=self.id, text=self.text, embedding=self.embedding, score=self.score, metadata=self.metadata)

    @staticmethod
    def from_entity(knowledge: Knowledge) -> "KnowledgeDto":
        return KnowledgeDto(
            id=knowledge.id,
            text=knowledge.text,
            embedding=knowledge.embedding,
            score=knowledge.score,
            metadata=knowledge.metadata,
        )


class KnowledgeQueryConfigDto(BaseModel):
    top_k: int | None = 3
    include_embedding: bool | None = True
    include_metadata: bool | None = True
    filter: dict[str, Any] | None = None

    def to_entity(self) -> KnowledgeQueryConfig:
        return KnowledgeQueryConfig(
            top_k=self.top_k,
            include_embedding=self.include_embedding,
            include_metadata=self.include_metadata,
            filter=self.filter,
        )


class KnowledgeQueryDto(BaseModel):
    text: str | None = None
    embedding: list[float] | None = None
    config: KnowledgeQueryConfigDto | None = KnowledgeQueryConfigDto()

    def to_entity(self) -> KnowledgeQuery:
        return KnowledgeQuery(
            text=self.text,
            embedding=self.embedding,
            config=self.config.to_entity() if self.config else None,
        )


class FederatedKnowledgeQueryDto(BaseModel):
    query: KnowledgeQueryDto
    providers: list[str] | None = []
    include_provider_contribution: bool | None = False
    knowledge_rerank_method: str | None = None

    def to_entity(self) -> FederatedKnowledgeQuery:
        return FederatedKnowledgeQuery(
            query=self.query.to_entity(),
            providers=[ConnectorId(value=provider_id) for provider_id in self.providers],
            include_provider_contribution=self.include_provider_contribution,
            knowledge_rerank_method=KnowledgeRerankMethod(value=self.knowledge_rerank_method)
            if self.knowledge_rerank_method
            else None,
        )
