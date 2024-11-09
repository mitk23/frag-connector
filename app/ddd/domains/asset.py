import abc
from typing import AsyncGenerator, ClassVar, Literal

from ddd.domains.base import BaseUUID4, ValueObject
from pydantic import BaseModel, ConfigDict, HttpUrl

# TODO: replace Asset --> dcat:Dataset


class DistributionBase(BaseModel):
    title: str
    description: str | None = None
    media_type: str | None = None

    def __eq__(self, obj: object) -> bool:
        return self.name == obj.name


class DistributionCatalog(DistributionBase):
    pass


class Distribution(DistributionBase):
    url: HttpUrl | None = None


class DistributionContent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    media_type: str | None = None
    content: bytes | None = None
    stream: AsyncGenerator[bytes, None] | None = None


class VectorFilter(BaseModel):
    has_metadata: dict[str, str | list[str]] | None = {}
    has_id: set[str] | None = set()


class AssetId(BaseUUID4):
    pass


class AssetSecurityLevel(ValueObject):
    CONFIDENTIAL: ClassVar[str] = "confidential"
    RESTRICTED: ClassVar[str] = "restricted"
    PUBLIC: ClassVar[str] = "public"

    value: Literal["confidential", "restricted", "public"]

    @classmethod
    def generate(cls, security_level=None) -> "AssetSecurityLevel":
        if security_level is None:
            return AssetSecurityLevel(value=cls.PUBLIC)
        return AssetSecurityLevel(value=security_level)

    @staticmethod
    def list_all() -> list["AssetSecurityLevel"]:
        values = [AssetSecurityLevel.CONFIDENTIAL, AssetSecurityLevel.RESTRICTED, AssetSecurityLevel.PUBLIC]
        return [AssetSecurityLevel(value=value) for value in values]

    def to_number(self) -> int:
        value_map = {
            AssetSecurityLevel.CONFIDENTIAL: 30,
            AssetSecurityLevel.RESTRICTED: 20,
            AssetSecurityLevel.PUBLIC: 10,
        }
        return value_map.get(self.value)


class AssetUsagePolicy(BaseModel):
    security_level: AssetSecurityLevel | None = AssetSecurityLevel.generate()


class AssetBase(BaseModel):
    id: AssetId | None
    title: str
    description: str | None = None
    usage_policy: AssetUsagePolicy | None = AssetUsagePolicy()

    def __eq__(self, obj: object) -> bool:
        return self.id == obj.id


class AssetCatalog(AssetBase):
    distributions: list[DistributionCatalog] | None = []


class Asset(AssetBase):
    distributions: list[Distribution] | None = []
    vectors: VectorFilter | None = None


class AssetRepositoryIF(abc.ABC):
    @abc.abstractmethod
    async def find_all(self) -> dict[AssetId, Asset]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(self, _id: AssetId) -> Asset | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def save(self, asset: Asset) -> Asset:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, _id: AssetId) -> None:
        raise NotImplementedError


# import abc
# import uuid
# from typing import ClassVar, Literal

# from core.exceptions import InternalException
# from ddd.domains.base import ValueObject
# from pydantic import UUID4, BaseModel, HttpUrl


# class AssetId(ValueObject):
#     value: UUID4

#     @staticmethod
#     def generate_id() -> UUID4:
#         return uuid.uuid4()

#     @staticmethod
#     def generate() -> "AssetId":
#         return AssetId(value=AssetId.generate_id())


# class AssetSecurityLevel(ValueObject):
#     CONFIDENTIAL: ClassVar[str] = "confidential"
#     RESTRICTED: ClassVar[str] = "restricted"
#     PUBLIC: ClassVar[str] = "public"

#     value: Literal["confidential", "restricted", "public"]

#     @classmethod
#     def generate(cls, security_level=None) -> "AssetSecurityLevel":
#         if security_level is None:
#             return AssetSecurityLevel(value=cls.PUBLIC)
#         return AssetSecurityLevel(value=security_level)


# class AssetBase(BaseModel):
#     id: AssetId | None
#     name: str
#     title: str | None = None
#     description: str | None = None
#     content_type: str | None = None

#     def __eq__(self, obj: object) -> bool:
#         return self.id == obj.id


# class Asset(AssetBase):
#     url: HttpUrl | None = None
#     security: AssetSecurityLevel | None = AssetSecurityLevel.generate()


# class AssetCatalog(AssetBase):
#     pass


# class AssetRepositoryIF(abc.ABC):
#     @abc.abstractmethod
#     async def find_all(self) -> dict[AssetId, Asset]:
#         raise NotImplementedError

#     @abc.abstractmethod
#     async def find_by_id(self, _id: AssetId) -> Asset | None:
#         raise NotImplementedError

#     @abc.abstractmethod
#     async def save(self, asset: Asset) -> Asset:
#         raise NotImplementedError

#     @abc.abstractmethod
#     async def delete(self, _id: AssetId) -> None:
#         raise NotImplementedError

#     def __handle_error(self, error: Exception, description: str):
#         raise InternalException(description=description, upstream_exc=error)
