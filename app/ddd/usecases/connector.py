from core.exceptions import ConnectorException
from ddd.domains.connector import Connector, ConnectorId, ConnectorRepositoryIF, ConnectorTrustLevel
from fastapi import status

from .schemas.connector import ConnectorCreateDto, ConnectorDto, ConnectorUpdateDto


class ConnectorUsecase:
    def __init__(self, connector_repository: ConnectorRepositoryIF):
        self.__connector_repository = connector_repository

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_connectors(self) -> dict[str, ConnectorDto]:
        connectors = await self.__connector_repository.find_all()
        return {str(_id): ConnectorDto.from_entity(asset) for _id, asset in connectors.items()}

    async def list_connectors_by_trust_level(self, trust_level: str) -> dict[str, ConnectorDto]:
        trust_level_map: dict[str, int] = {
            ConnectorTrustLevel.LOW: 10,
            ConnectorTrustLevel.MEDIUM: 20,
            ConnectorTrustLevel.HIGH: 30,
        }

        connectors = await self.__connector_repository.find_all()
        connectors_dto = {str(_id): ConnectorDto.from_entity(connector) for _id, connector in connectors.items()}

        connectors_dto_by_level = {}
        for _id, connector in connectors_dto.items():
            if trust_level_map[connector.trust] >= trust_level_map[trust_level]:
                connectors_dto_by_level[_id] = connector
        return connectors_dto_by_level

    async def get_connector(self, connector_id: str) -> ConnectorDto:
        connector = await self.__connector_repository.find_by_id(ConnectorId(value=connector_id))
        if connector is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Connector ID={connector_id}` not found"
            )
        return ConnectorDto.from_entity(connector)

    async def create_connector(self, new_connector: ConnectorCreateDto) -> ConnectorDto:
        connectors = await self.__connector_repository.find_all()

        for connector in connectors.values():
            if connector.name == new_connector.name:
                self.__handle_error(
                    status_code=status.HTTP_409_CONFLICT,
                    description=f"Connector `{new_connector.name}` is already registered",
                )

        new_connector = Connector(
            id=None,
            name=new_connector.name,
            url=new_connector.url,
            trust=ConnectorTrustLevel.generate(new_connector.trust),
        )
        try:
            created_connector = await self.__connector_repository.save(new_connector)
        except Exception as exc:
            self.__handle_error(description="Failed to create a new connector", error=exc)

        return ConnectorDto.from_entity(created_connector)

    async def update_connector(self, connector_id: str, new_connector: ConnectorUpdateDto) -> None:
        old_connector = await self.__connector_repository.find_by_id(ConnectorId(value=connector_id))

        if old_connector is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Connector ID={connector_id}` not found"
            )
        if connector_id != new_connector.id:
            self.__handle_error(status_code=status.HTTP_400_BAD_REQUEST, description="Invalid connector update request")

        new_connector_dto = ConnectorDto.model_validate(new_connector.model_dump())
        new_connector_entity = new_connector_dto.to_entity()

        try:
            await self.__connector_repository.save(new_connector_entity)
        except Exception as exc:
            self.__handle_error(description=f"Failed to update the connector: {connector_id}", error=exc)

    async def delete_connector(self, connector_id: str) -> None:
        try:
            await self.__connector_repository.delete(ConnectorId(value=connector_id))
        except Exception as exc:
            self.__handle_error(description=f"Failed to delete the connector: {connector_id}", error=exc)
