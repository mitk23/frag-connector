import abc
import uuid
from typing import ClassVar, Literal

from core.exceptions import InternalException
from ddd.domains.base import ValueObject
from pydantic import UUID4, BaseModel, HttpUrl


class AssetId(ValueObject):
    value: UUID4

    @staticmethod
    def generate_id() -> UUID4:
        return uuid.uuid4()

    @staticmethod
    def generate() -> "AssetId":
        return AssetId(value=AssetId.generate_id())


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


class AssetBase(BaseModel):
    id: AssetId | None
    name: str
    title: str | None = None
    description: str | None = None
    content_type: str | None = None

    def __eq__(self, obj: object) -> bool:
        return self.id == obj.id


class Asset(AssetBase):
    url: HttpUrl | None = None
    security: AssetSecurityLevel | None = AssetSecurityLevel.generate()


class AssetCatalog(AssetBase):
    pass



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

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)
