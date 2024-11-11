import abc
import heapq
from typing import Any, ClassVar, Generator, Literal

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


class FederatedKnowledgeQuery(BaseModel):
    query: KnowledgeQuery
    providers: list[ConnectorId] | None = []
    include_provider_contribution: bool | None = False
    knowledge_rerank_method: KnowledgeRerankMethod | None = KnowledgeRerankMethod()


class FederatedKnowledgeQueryResult(BaseModel):
    result: dict[ConnectorId, list[Knowledge]]

    def __rerank_naive(self, top_k: int):
        """
        extract Top-K knowledges by its similarity score
        """
        # heap[Score, ConnectorId, Index]
        heap: list[tuple[float, ConnectorId, int]] = []

        for provider, knowledges in self.result.items():
            if len(knowledges) == 0:
                continue
            top_knowledge_score = knowledges[0].score
            heapq.heappush(heap, (-top_knowledge_score, provider, 0))

        reranked_knowledges: list[Knowledge] = []
        for _ in range(top_k):
            if len(heap) == 0:
                break

            _, provider, idx = heapq.heappop(heap)

            knowledge = self.result.get(provider)[idx]
            # TODO: Contribution対応
            # if knowledge.metadata is None:
            #     knowledge.metadata = {"provider": str(provider)}
            # else:
            #     knowledge.metadata |= {"provider": str(provider)}
            reranked_knowledges.append(knowledge)

            if idx + 1 < len(self.result.get(provider)):
                next_knowledge_score = self.result.get(provider)[idx + 1].score
                heapq.heappush(heap, (-next_knowledge_score, provider, idx + 1))
        return reranked_knowledges

    def __rerank_cosine(self, top_k: int, query_embedding: list[float]):
        def cosine_similarity(x: list[float], y: list[float]) -> float:
            import numpy as np

            return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))

        # heap[Score, ConnectorId, Knowledge]
        heap: list[tuple[float, ConnectorId, Knowledge]] = []

        for provider, knowledges in self.result.items():
            for knowledge in knowledges:
                new_score = cosine_similarity(knowledge.embedding, query_embedding)
                knowledge.score = new_score
                heapq.heappush(heap, (new_score, provider, knowledge))

        top_k_knowledges = heapq.nlargest(top_k, heap, key=lambda ele: ele[0])
        return [knowledge for _, _, knowledge in top_k_knowledges]

    def rerank(
        self, method: KnowledgeRerankMethod, top_k: int = 3, query_embedding: list[float] | None = None
    ) -> list[Knowledge]:
        if str(method) == KnowledgeRerankMethod.NAIVE:
            return self.__rerank_naive(top_k)
        elif str(method) == KnowledgeRerankMethod.COSINE:
            if query_embedding is None:
                raise ValueError("query_embedding is required")
            return self.__rerank_cosine(top_k, query_embedding)
        else:
            raise ValueError("Unsupported rerank method")


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
