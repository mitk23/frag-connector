from typing import Any

from ddd.domains.knowledge import Knowledge, KnowledgeQuery
from pydantic import BaseModel
from qdrant_client.models import Filter, SearchParams


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
    query_vector: list[float]
    limit: int | None = 3
    with_vectors: bool | None = True
    with_payload: bool | None = True
    query_filter: Filter | None = None
    search_params: SearchParams | None = None

    @staticmethod
    def from_entity(query: KnowledgeQuery) -> "KnowledgeQueryQdrantDao":
        return KnowledgeQueryQdrantDao(
            query_vector=query.embedding,
            limit=query.config.top_k,
            with_vectors=query.config.include_embedding,
            with_payload=query.config.include_metadata,
            query_filter=Filter.model_validate(query.config.filter) if query.config.filter else None,
            search_params=SearchParams(exact=query.config.exact_search),
        )
