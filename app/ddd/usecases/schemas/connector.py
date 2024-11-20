from ddd.domains.connector import Connector, ConnectorId, ConnectorTrustLevel
from pydantic import BaseModel


class ConnectorDtoBase(BaseModel):
    id: str
    url: str
    trust: str | None = None


class ConnectorCreateDto(ConnectorDtoBase):
    pass


class ConnectorUpdateDto(ConnectorDtoBase):
    pass


class ConnectorDto(ConnectorDtoBase):
    def to_entity(self) -> Connector:
        return Connector(id=ConnectorId(value=self.id), url=self.url, trust=ConnectorTrustLevel(value=self.trust))

    @staticmethod
    def from_entity(connector: Connector) -> "ConnectorDto":
        return ConnectorDto(id=str(connector.id), url=str(connector.url), trust=str(connector.trust))
