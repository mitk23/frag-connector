from typing import Literal

from pydantic import UUID4, BaseModel, HttpUrl

from .base import BaseApiSchema


class DistributionBase(BaseModel):
    title: str
    description: str | None = None
    media_type: str | None = None


class DistributionCatalog(DistributionBase):
    pass


class Distribution(DistributionBase):
    url: HttpUrl | None = None


class VectorFilter(BaseModel):
    has_metadata: dict[str, str | list[str]] | None = {}
    has_id: set[str] | None = set()


class AssetUsagePolicy(BaseModel):
    security_level: Literal["confidential", "restricted", "public"] | None = "public"


class AssetBase(BaseApiSchema):
    title: str
    description: str | None = None
    usage_policy: AssetUsagePolicy | None = AssetUsagePolicy()


class AssetCatalogResponse(AssetBase):
    id: UUID4
    distributions: list[DistributionCatalog]


class AssetCreateRequest(AssetBase):
    distributions: list[Distribution] | None = []
    vectors: VectorFilter | None = None


class AssetUpdateRequest(AssetBase):
    id: UUID4
    distributions: list[Distribution] | None = []
    vectors: VectorFilter | None = None


class AssetResponse(AssetBase):
    id: UUID4
    distributions: list[Distribution]
    vectors: VectorFilter | None = None
