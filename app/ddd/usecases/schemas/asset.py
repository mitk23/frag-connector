from ddd.domains.asset import Asset, AssetCatalog, AssetId, AssetSecurityLevel
from pydantic import BaseModel


class AssetDtoBase(BaseModel):
    name: str
    url: str | None = None
    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    security: str | None = None


class AssetCreateDto(AssetDtoBase):
    pass


class AssetUpdateDto(AssetDtoBase):
    id: str


class AssetDto(AssetDtoBase):
    id: str

    def to_entity(self) -> Asset:
        return Asset(
            id=AssetId(value=self.id),
            name=self.name,
            url=self.url,
            title=self.title,
            description=self.description,
            content_type=self.content_type,
            security=AssetSecurityLevel.generate(self.security),
        )

    @staticmethod
    def from_entity(asset: Asset) -> "AssetDto":
        return AssetDto(
            id=str(asset.id),
            name=asset.name,
            url=str(asset.url) if asset.url else None,
            title=asset.title,
            description=asset.description,
            content_type=asset.content_type,
            security=str(asset.security),
        )


class AssetCatalogDto(BaseModel):
    id: str
    name: str
    title: str | None = None
    description: str | None = None
    content_type: str | None = None

    def to_entity(self) -> AssetCatalog:
        return AssetCatalog(
            id=AssetId(value=self.id),
            name=self.name,
            title=self.title,
            description=self.description,
            content_type=self.content_type,
        )

    @staticmethod
    def from_entity(asset: AssetCatalog) -> "AssetCatalogDto":
        return AssetCatalogDto(
            id=str(asset.id),
            name=asset.name,
            title=asset.title,
            description=asset.description,
            content_type=asset.content_type,
        )
