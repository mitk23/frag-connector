from typing import Any

from ddd.domains.knowledge import Knowledge, KnowledgeQuery
from pydantic import BaseModel


class KnowledgePineconeDao(BaseModel):
    id: str
    values: list[float] | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None
    sparseValues: dict | None = None

    def to_entity(self, text_key_in_metadata="text") -> Knowledge:
        text_in_metadata = self.metadata.get(text_key_in_metadata) if self.metadata else None
        return Knowledge(
            id=self.id, text=text_in_metadata, embedding=self.values, score=self.score, metadata=self.metadata
        )


class KnowledgeQueryPineconeDao(BaseModel):
    vector: list[float]
    top_k: int | None = 3
    include_values: bool | None = True
    include_metadata: bool | None = True
    filter: dict[str, Any] | None = None

    @staticmethod
    def from_entity(query: KnowledgeQuery) -> "KnowledgeQueryPineconeDao":
        return KnowledgeQueryPineconeDao(
            vector=query.embedding,
            top_k=query.config.top_k,
            include_values=query.config.include_embedding,
            include_metadata=query.config.include_metadata,
            filter=query.config.filter,
        )


class KnowledgeQueryResponsePineconeDao(BaseModel):
    matches: list[KnowledgePineconeDao]
    namespace: str
    usage: dict | None = None


class KnowledgeFetchResponsePineconeDao(BaseModel):
    vectors: dict[str, KnowledgePineconeDao]
    namespace: str
    usage: dict | None = None
