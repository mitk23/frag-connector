import abc
from typing import ClassVar, Literal

from ddd.domains.base import ValueObject
from pydantic import BaseModel, HttpUrl


class ConnectorId(ValueObject):
    value: str


class ConnectorTrustLevel(ValueObject):
    LOW: ClassVar[str] = "low"
    MEDIUM: ClassVar[str] = "medium"
    HIGH: ClassVar[str] = "high"

    value: Literal["low", "medium", "high"]

    def to_number(self) -> int:
        value_map = {
            ConnectorTrustLevel.HIGH: 30,
            ConnectorTrustLevel.MEDIUM: 20,
            ConnectorTrustLevel.LOW: 10,
        }
        return value_map.get(self.value)


class Connector(BaseModel):
    id: ConnectorId
    url: HttpUrl
    trust: ConnectorTrustLevel | None = ConnectorTrustLevel(value=ConnectorTrustLevel.LOW)

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
