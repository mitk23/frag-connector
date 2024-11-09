from typing import AsyncGenerator

from ddd.domains.asset import (
    Asset,
    AssetCatalog,
    AssetId,
    AssetSecurityLevel,
    AssetUsagePolicy,
    Distribution,
    DistributionCatalog,
    DistributionContent,
    VectorFilter,
)
from pydantic import BaseModel, ConfigDict


class DistributionDtoBase(BaseModel):
    title: str
    description: str | None = None
    media_type: str | None = None


class DistributionCatalogDto(DistributionDtoBase):
    def to_entity(self) -> DistributionCatalog:
        return DistributionCatalog(
            title=self.title,
            description=self.description,
            media_type=self.media_type,
        )

    @staticmethod
    def from_entity(distribution: Distribution | DistributionCatalog) -> "DistributionCatalogDto":
        return DistributionCatalogDto(
            title=distribution.title,
            description=distribution.description,
            media_type=distribution.media_type,
        )


class DistributionDto(DistributionDtoBase):
    url: str | None = None

    def to_entity(self) -> Distribution:
        return Distribution(
            title=self.title,
            description=self.description,
            media_type=self.media_type,
            url=self.url,
        )

    @staticmethod
    def from_entity(distribution: Distribution) -> "DistributionDto":
        return DistributionDto(
            title=distribution.title,
            description=distribution.description,
            media_type=distribution.media_type,
            url=str(distribution.url) if distribution.url else None,
        )


class DistributionContentDto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    media_type: str | None = None
    content: bytes | None = None
    stream: AsyncGenerator[bytes, None] | None = None

    @staticmethod
    def from_entity(content: DistributionContent):
        return DistributionContentDto(media_type=content.media_type, content=content.content, stream=content.stream)


class VectorFilterDto(BaseModel):
    has_metadata: dict[str, str | list[str]] | None
    has_id: set[str] | None

    def to_entity(self) -> VectorFilter:
        return VectorFilter(has_metadata=self.has_metadata, has_id=self.has_id)

    @staticmethod
    def from_entity(vectors: VectorFilter) -> "VectorFilterDto":
        return VectorFilterDto(has_metadata=vectors.has_metadata, has_id=vectors.has_id)


class AssetUsagePolicyDto(BaseModel):
    security_level: str | None = None

    def to_entity(self) -> AssetUsagePolicy:
        return AssetUsagePolicy(security_level=AssetSecurityLevel(value=self.security_level))

    @staticmethod
    def from_entity(policy: AssetUsagePolicy) -> "AssetUsagePolicyDto":
        return AssetUsagePolicyDto(security_level=str(policy.security_level))


class AssetDtoBase(BaseModel):
    title: str
    description: str | None = None
    usage_policy: AssetUsagePolicyDto | None = None


class AssetCatalogDto(AssetDtoBase):
    id: str
    distributions: list[DistributionCatalogDto]

    def to_entity(self) -> AssetCatalog:
        return AssetCatalog(
            id=AssetId(value=self.id),
            title=self.title,
            description=self.description,
            usage_policy=self.usage_policy.to_entity() if self.usage_policy else None,
            distributions=[distribution.to_entity() for distribution in self.distributions],
        )

    @staticmethod
    def from_entity(asset: AssetCatalog | Asset) -> "AssetCatalogDto":
        return AssetCatalogDto(
            id=str(asset.id),
            title=asset.title,
            description=asset.description,
            usage_policy=AssetUsagePolicyDto.from_entity(asset.usage_policy) if asset.usage_policy else None,
            distributions=[DistributionCatalogDto.from_entity(distribution) for distribution in asset.distributions],
        )


class AssetDto(AssetDtoBase):
    id: str
    distributions: list[DistributionDto]
    vectors: VectorFilterDto | None = None

    def to_entity(self) -> Asset:
        return Asset(
            id=AssetId(value=self.id),
            title=self.title,
            description=self.description,
            usage_policy=self.usage_policy.to_entity() if self.usage_policy else None,
            distributions=[distribution.to_entity() for distribution in self.distributions],
            vectors=self.vectors.to_entity() if self.vectors else None,
        )

    @staticmethod
    def from_entity(asset: Asset) -> "AssetDto":
        return AssetDto(
            id=str(asset.id),
            title=asset.title,
            description=asset.description,
            usage_policy=AssetUsagePolicyDto.from_entity(asset.usage_policy) if asset.usage_policy else None,
            distributions=[DistributionDto.from_entity(distribution) for distribution in asset.distributions],
            vectors=VectorFilterDto.from_entity(asset.vectors) if asset.vectors else None,
        )


class AssetCreateDto(AssetDtoBase):
    distributions: list[DistributionDto]
    vectors: VectorFilterDto | None


class AssetUpdateDto(AssetDtoBase):
    id: str
    distributions: list[DistributionDto]
    vectors: VectorFilterDto | None
