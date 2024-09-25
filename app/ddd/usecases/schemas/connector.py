from ddd.domains.connector import Connector, ConnectorId, ConnectorTrustLevel
from pydantic import BaseModel


class ConnectorDtoBase(BaseModel):
    name: str
    url: str
    trust: str | None = None


class ConnectorCreateDto(ConnectorDtoBase):
    pass


class ConnectorUpdateDto(ConnectorDtoBase):
    id: str


class ConnectorDto(ConnectorDtoBase):
    id: str

    def to_entity(self) -> Connector:
        return Connector(
            id=ConnectorId(value=self.id), name=self.name, url=self.url, trust=ConnectorTrustLevel.generate(self.trust)
        )

    @staticmethod
    def from_entity(connector: Connector) -> "ConnectorDto":
        return ConnectorDto(
            id=str(connector.id), name=connector.name, url=str(connector.url), trust=str(connector.trust)
        )
