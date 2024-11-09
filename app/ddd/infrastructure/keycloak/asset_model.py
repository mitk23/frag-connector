from ddd.domains.asset import Asset, AssetId
from pydantic import AliasChoices, BaseModel, Field


class AssetKeycloakDaoAttributes(BaseModel):
    description: list[str] | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"description": self.description[0] if self.description else None}


class AssetKeycloakDao(BaseModel):
    id: str | None = Field(validation_alias=AliasChoices("id", "_id"))
    name: str
    attributes: AssetKeycloakDaoAttributes | None = AssetKeycloakDaoAttributes()
    ownerManagedAccess: bool | None = True

    def to_entity(self) -> Asset:
        attributes_dict = self.attributes.to_dict()
        # notice: some fields (usage_policy, disributions) are missing, set to default
        return Asset(
            id=AssetId(value=self.id) if self.id else None,
            title=self.name,
            description=attributes_dict["description"],
        )

    @staticmethod
    def from_entity(asset: Asset) -> "AssetKeycloakDao":
        return AssetKeycloakDao(
            id=str(asset.id) if asset.id else None,
            name=asset.title,
            attributes=AssetKeycloakDaoAttributes(
                description=[asset.description] if asset.description else None,
            ),
        )
