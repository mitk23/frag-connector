from typing import Literal

from pydantic import UUID4, BaseModel, HttpUrl


class BaseApiSchema(BaseModel):
    def to_dict(self):
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, dic: dict):
        return cls.model_validate(dic)


class AssetBase(BaseApiSchema):
    name: str
    url: HttpUrl | None = None
    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    security: Literal["confidential", "restricted", "public"] | None = "public"


class AssetCreateRequest(AssetBase):
    pass


class AssetUpdateRequest(AssetBase):
    id: UUID4


class AssetResponse(AssetBase):
    id: UUID4


class AssetCatalogBase(BaseApiSchema):
    id: UUID4
    name: str
    title: str | None = None
    description: str | None = None
    content_type: str | None = None


class AssetCatalogResponse(AssetCatalogBase):
    id: UUID4


class ConnectorBase(BaseApiSchema):
    name: str
    url: str
    trust: Literal["low", "medium", "high"] | None = "low"


class ConnectorCreateRequest(ConnectorBase):
    pass


class ConnectorUpdateRequest(ConnectorBase):
    id: UUID4


class ConnectorResponse(ConnectorBase):
    id: UUID4


class AssetRequest(BaseModel):
    asset_id: str
    provider: str


class RetrieveRequest(BaseModel):
    query_vector: list[float]
    top_k: int = 3
    include_vector: bool = False
    include_contribution: bool = False
    retrieval_providers: list[str] | None = None
    rerank: Literal["naive"] | None = None


class GenerateRequest(BaseModel):
    model: str
    user_prompt: str
    llm_connector: str | None = None
    system_prompt: str | None = None


class FRAGRequest(BaseModel):
    # Retrieval
    query_vector: list[float]
    top_k: int = 3
    include_contribution: bool = False
    retrieval_providers: list[str] | None = None
    rerank: Literal["naive"] | None = None
    # Generation
    query_text: str
    model: str
    llm_connector: str | None = None
