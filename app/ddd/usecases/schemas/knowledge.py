from typing import Any

from ddd.domains.connector import ConnectorId
from ddd.domains.knowledge import (
    FederatedKnowledge,
    FederatedKnowledgeList,
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
    exact_search: bool | None = False

    def to_entity(self) -> KnowledgeQueryConfig:
        return KnowledgeQueryConfig(
            top_k=self.top_k,
            include_embedding=self.include_embedding,
            include_metadata=self.include_metadata,
            filter=self.filter,
            exact_search=self.exact_search,
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


class FederatedKnowledgeDto(KnowledgeDto):
    provider: str

    def to_entity(self) -> FederatedKnowledge:
        return FederatedKnowledge(
            id=self.id,
            text=self.text,
            embedding=self.embedding,
            score=self.score,
            metadata=self.metadata,
            provider=ConnectorId(value=self.provider),
        )

    @staticmethod
    def from_entity(knowledge: FederatedKnowledge) -> "FederatedKnowledgeDto":
        return FederatedKnowledgeDto(
            id=knowledge.id,
            text=knowledge.text,
            embedding=knowledge.embedding,
            score=knowledge.score,
            metadata=knowledge.metadata,
            provider=str(knowledge.provider),
        )


class FederatedKnowledgeListDto(BaseModel):
    knowledge_list: list[FederatedKnowledgeDto]
    __index: int = 0

    def __iter__(self):
        return self

    def __next__(self) -> FederatedKnowledgeDto:
        if self.__index == len(self.knowledge_list):
            raise StopIteration()
        value = self.knowledge_list[self.__index]
        self.__index += 1
        return value

    @staticmethod
    def from_entity(knowledge_list: FederatedKnowledgeList) -> "FederatedKnowledgeListDto":
        return FederatedKnowledgeListDto(
            knowledge_list=[FederatedKnowledgeDto.from_entity(knowledge) for knowledge in knowledge_list]
        )


class FederatedKnowledgeQueryDto(BaseModel):
    query: KnowledgeQueryDto
    providers: list[str] | None = []
    knowledge_rerank_method: str | None = None
    return_num_knowledges: int | None

    def to_entity(self) -> FederatedKnowledgeQuery:
        return FederatedKnowledgeQuery(
            query=self.query.to_entity(),
            providers=[ConnectorId(value=provider_id) for provider_id in self.providers],
            knowledge_rerank_method=KnowledgeRerankMethod(value=self.knowledge_rerank_method)
            if self.knowledge_rerank_method
            else None,
            return_num_knowledges=self.return_num_knowledges,
        )
