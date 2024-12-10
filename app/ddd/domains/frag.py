from typing import Any

from ddd.domains.connector import ConnectorId
from pydantic import BaseModel

from .knowledge import KnowledgeRerankMethod


class RetrievalParams(BaseModel):
    top_k: int
    filter: dict[str, Any] | None
    exact_search: bool


class FederatedRAGQueryContent(BaseModel):
    text: str
    embedding: list[float]


class FederatedRetrievalConfig(BaseModel):
    retrieval_params: RetrievalParams
    retrieval_providers: list[ConnectorId]
    number_of_knowledges: int
    rerank_knowledges_by: KnowledgeRerankMethod


class GenerationConfig(BaseModel):
    llm_provider: ConnectorId
    llm_model: str


class FederatedRAGQuery(BaseModel):
    query: FederatedRAGQueryContent
    retrieval: FederatedRetrievalConfig
    generation: GenerationConfig
