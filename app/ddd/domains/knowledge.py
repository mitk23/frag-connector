import abc
import heapq
from typing import Any, ClassVar, Generator, Literal

import numpy as np
from ddd.domains.connector import ConnectorId
from pydantic import BaseModel

from .base import ValueObject


class Knowledge(BaseModel):
    id: str | None = None
    text: str | None = None
    embedding: list[float] | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None

    def __eq__(self, obj: object) -> bool:
        return self.id == obj.id

    def __lt__(self, obj: object) -> bool:
        return self.id < obj.id


class KnowledgeQueryConfig(BaseModel):
    top_k: int | None = 3
    include_embedding: bool | None = True
    include_metadata: bool | None = True
    filter: dict[str, Any] | None = None


class KnowledgeQuery(BaseModel):
    text: str | None = None
    embedding: list[float] | None = None
    config: KnowledgeQueryConfig | None = KnowledgeQueryConfig()


class KnowledgeRerankMethod(ValueObject):
    NAIVE: ClassVar[str] = "naive"
    COSINE: ClassVar[str] = "cosine"

    value: Literal["naive", "cosine"] | None = "naive"


class FederatedKnowledge(Knowledge):
    provider: ConnectorId

    @staticmethod
    def from_knowledge(knowledge: Knowledge, provider: ConnectorId) -> "FederatedKnowledge":
        return FederatedKnowledge(provider=provider, **knowledge.model_dump())


class FederatedKnowledgeList(BaseModel):
    knowledge_list: list[FederatedKnowledge] | None = []
    __index: int = 0

    def __iter__(self):
        return self

    def __next__(self) -> FederatedKnowledge:
        if self.__index == len(self.knowledge_list):
            raise StopIteration()
        value = self.knowledge_list[self.__index]
        self.__index += 1
        return value

    def append(self, knowledge: FederatedKnowledge) -> None:
        self.knowledge_list.append(knowledge)

    def append_list(self, knowledges: list[FederatedKnowledge]) -> None:
        self.knowledge_list += knowledges

    def rerank(
        self, method: KnowledgeRerankMethod, top_k: int = 5, query_embedding: list[float] | None = None
    ) -> "FederatedKnowledgeList":
        if str(method) == KnowledgeRerankMethod.NAIVE:
            return self.__rerank_naive(top_k)
        elif str(method) == KnowledgeRerankMethod.COSINE:
            if query_embedding is None:
                raise ValueError("query_embedding is required")
            return self.__rerank_cosine(top_k, query_embedding)
        else:
            raise ValueError("Unsupported rerank method")

    def __rerank_naive(self, top_k: int) -> "FederatedKnowledgeList":
        """
        extract Top-K knowledges by its similarity score
        """
        # heap[tuple[float, FederatedKnowledge]]
        heap: list[tuple[float, FederatedKnowledge]] = []

        for knowledge in self.knowledge_list:
            heapq.heappush(heap, (knowledge.score, knowledge))

        top_k_knowledges = heapq.nlargest(min(top_k, len(self.knowledge_list)), heap, key=lambda tup: tup[0])
        return FederatedKnowledgeList(knowledge_list=[knowledge for _, knowledge in top_k_knowledges])

    def __rerank_cosine(self, top_k: int, query_embedding: list[float]) -> "FederatedKnowledgeList":
        def cosine_similarity(x: list[float], y: list[float]) -> float:
            return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))

        # heap[tuple[float, FederatedKnowledge]]
        heap: list[tuple[float, FederatedKnowledge]] = []

        for knowledge in self.knowledge_list:
            new_score = cosine_similarity(knowledge.embedding, query_embedding)
            knowledge.score = new_score
            heapq.heappush(heap, (new_score, knowledge))

        top_k_knowledges = heapq.nlargest(min(top_k, len(self.knowledge_list)), heap, key=lambda tup: tup[0])
        return FederatedKnowledgeList(knowledge_list=[knowledge for _, knowledge in top_k_knowledges])


class FederatedKnowledgeQuery(BaseModel):
    query: KnowledgeQuery
    providers: list[ConnectorId] | None = []
    knowledge_rerank_method: KnowledgeRerankMethod | None = KnowledgeRerankMethod()
    return_num_knowledges: int | None


class KnowledgeQueryServiceIF(abc.ABC):
    @abc.abstractmethod
    async def execute(self, query: KnowledgeQuery) -> list[Knowledge]:
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch(self, knowledge_id_list: list[str]) -> list[Knowledge]:
        raise NotImplementedError


class Question(BaseModel):
    text: str


class Answer(BaseModel):
    text: Generator[str, None, None]


class QAServiceIF(abc.ABC):
    @abc.abstractmethod
    async def ask(self, question: Question, knowledges: list[Knowledge] | None) -> Answer:
        raise NotImplementedError


# class LLMQuery(BaseModel):
#     model: str
#     user_prompt: str
#     system_prompt: str | None = None
