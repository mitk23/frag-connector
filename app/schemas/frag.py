from typing import Any, Literal

from ddd.domains.frag import FederatedRAGQueryContent
from pydantic import BaseModel


class RetrievalParamsRequest(BaseModel):
    top_k: int | None = 10
    filter: dict[str, Any] | None = None
    exact_search: bool | None = False


class FederatedRetrievalConfigRequest(BaseModel):
    retrieval_params: RetrievalParamsRequest | None = RetrievalParamsRequest()
    retrieval_providers: list[str]
    number_of_knowledges: int | None = 10
    rerank_knowledges_by: Literal["naive", "cosine"] | None = "cosine"


class GenerationConfigRequest(BaseModel):
    llm_provider: str
    llm_model: str


class FederatedRAGRequest(BaseModel):
    query: FederatedRAGQueryContent
    retrieval: FederatedRetrievalConfigRequest
    generation: GenerationConfigRequest
