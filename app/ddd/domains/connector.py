import abc
import uuid
from typing import ClassVar, Literal

from core.exceptions import InternalException
from ddd.domains.base import ValueObject
from pydantic import UUID4, BaseModel, HttpUrl


# TODO: uuidは本来keycloak側で発行されるもの -> localではclient_idによる識別のみを行う
class ConnectorId(ValueObject):
    value: UUID4

    @classmethod
    def generate(cls) -> "ConnectorId":
        return cls(value=uuid.uuid4())


class ConnectorTrustLevel(ValueObject):
    LOW: ClassVar[str] = "low"
    MEDIUM: ClassVar[str] = "medium"
    HIGH: ClassVar[str] = "high"

    value: Literal["low", "medium", "high"]

    @classmethod
    def generate(cls, trust_level=None) -> "ConnectorTrustLevel":
        if trust_level is None:
            return ConnectorTrustLevel(value=cls.LOW)
        return ConnectorTrustLevel(value=trust_level)


class Connector(BaseModel):
    id: ConnectorId | None
    name: str
    url: HttpUrl
    trust: ConnectorTrustLevel | None = ConnectorTrustLevel.generate()

    def __eq__(self, obj: object) -> bool:
        return self.id == obj.id


class ConnectorRepositoryIF(abc.ABC):
    @abc.abstractmethod
    async def find_all(self) -> dict[ConnectorId, Connector]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(self, _id: ConnectorId) -> Connector | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def save(self, connector: Connector) -> Connector:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, _id: ConnectorId) -> None:
        raise NotImplementedError

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)
