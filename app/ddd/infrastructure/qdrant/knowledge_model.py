from typing import Any

from ddd.domains.knowledge import Knowledge, KnowledgeQuery
from pydantic import BaseModel


class KnowledgeQdrantDao(BaseModel):
    id: str | int
    vector: list[float] | None = None
    score: float | None = None
    payload: dict[str, Any] | None = None

    def to_entity(self, text_key_in_metadata="text") -> Knowledge:
        text_in_metadata = self.payload.get(text_key_in_metadata) if self.payload else None
        return Knowledge(
            id=str(self.id), text=text_in_metadata, embedding=self.vector, score=self.score, metadata=self.payload
        )


class KnowledgeQueryQdrantDao(BaseModel):
    # TODO: implement filter
    query_vector: list[float]
    limit: int | None = 3
    with_vectors: bool | None = True
    with_payload: bool | None = True

    @staticmethod
    def from_entity(query: KnowledgeQuery) -> "KnowledgeQueryQdrantDao":
        return KnowledgeQueryQdrantDao(
            query_vector=query.embedding,
            limit=query.config.top_k,
            with_vectors=query.config.include_embedding,
            with_payload=query.config.include_metadata,
        )
