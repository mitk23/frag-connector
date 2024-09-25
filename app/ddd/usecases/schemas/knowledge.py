from typing import Any

from ddd.domains.knowledge import Knowledge, KnowledgeQuery, KnowledgeQueryConfig
from pydantic import BaseModel


class KnowledgeDto(BaseModel):
    id: str | None = None
    text: str | None = None
    embedding: list[float] | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None

    def to_entity(self) -> Knowledge:
        pass

    @staticmethod
    def from_entity(knowledge: Knowledge) -> "KnowledgeDto":
        pass


class KnowledgeQueryDto(BaseModel):
    text: str | None = None
    embedding: list[float] | None = None
    top_k: int | None = 3
    include_embedding: bool | None = True
    include_metadata: bool | None = True
    filter: dict[str, Any] | None = None

    def to_entity(self) -> KnowledgeQuery:
        return KnowledgeQuery(
            text=self.text,
            embedding=self.embedding,
            config=KnowledgeQueryConfig(
                top_k=self.top_k,
                include_embedding=self.include_embedding,
                include_metadata=self.include_metadata,
                filter=self.filter,
            ),
        )
