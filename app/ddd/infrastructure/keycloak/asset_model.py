from ddd.domains.asset import Asset, AssetId, AssetSecurityLevel
from pydantic import AliasChoices, BaseModel, Field


class AssetKeycloakDaoAttributes(BaseModel):
    title: list[str] | None = None
    description: list[str] | None = None
    content_type: list[str] | None = None
    security: list[str] | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "title": self.title[0] if self.title else None,
            "description": self.description[0] if self.description else None,
            "content_type": self.content_type[0] if self.content_type else None,
            "security": self.security[0] if self.security else None,
        }


class AssetKeycloakDao(BaseModel):
    id: str | None = Field(validation_alias=AliasChoices("id", "_id"))
    name: str
    uris: list[str] | None = None
    attributes: AssetKeycloakDaoAttributes | None = AssetKeycloakDaoAttributes()
    ownerManagedAccess: bool | None = True

    def to_entity(self) -> Asset:
        attributes_dict = self.attributes.to_dict()
        return Asset(
            id=AssetId(value=self.id) if self.id else None,
            name=self.name,
            url=self.uris[0] if self.uris else None,
            title=attributes_dict["title"],
            description=attributes_dict["description"],
            content_type=attributes_dict["content_type"],
            security=AssetSecurityLevel.generate(attributes_dict["security"]),
        )

    @staticmethod
    def from_entity(asset: Asset) -> "AssetKeycloakDao":
        attributes_dao = AssetKeycloakDaoAttributes(
            title=[asset.title] if asset.title else None,
            description=[asset.description] if asset.description else None,
            content_type=[asset.content_type] if asset.content_type else None,
            security=[str(asset.security)] if asset.security else None,
        )
        return AssetKeycloakDao(
            id=str(asset.id) if asset.id else None,
            name=asset.name,
            uris=[str(asset.url)] if asset.url else None,
            attributes=attributes_dao,
        )
