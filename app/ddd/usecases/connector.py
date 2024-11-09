from core.exceptions import ConnectorException
from ddd.domains import domain_service
from ddd.domains.authorization import AuthRepositoryIF, Permission, PermissionBySecurityLevel
from ddd.domains.connector import Connector, ConnectorId, ConnectorRepositoryIF, ConnectorTrustLevel
from fastapi import status

from .schemas.connector import ConnectorCreateDto, ConnectorDto, ConnectorUpdateDto


class ConnectorQueryUsecase:
    def __init__(self, connector_repository: ConnectorRepositoryIF):
        self.__connector_repository = connector_repository

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_connectors(self) -> dict[str, ConnectorDto]:
        connectors = await self.__connector_repository.find_all()
        return {str(_id): ConnectorDto.from_entity(asset) for _id, asset in connectors.items()}

    async def get_connector(self, connector_id: str) -> ConnectorDto:
        connector = await self.__connector_repository.find_by_id(ConnectorId(value=connector_id))
        if connector is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Connector [{connector_id}] not found"
            )
        return ConnectorDto.from_entity(connector)


class ConnectorCommandUsecase:
    def __init__(self, connector_repository: ConnectorRepositoryIF, auth_repository: AuthRepositoryIF):
        self.__connector_repository = connector_repository
        self.__auth_repository = auth_repository

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def __list_permission_to_trust_level(self, trust_level: ConnectorTrustLevel) -> list[Permission]:
        authorized_asset_security_levels = domain_service.list_connector_accessible_asset_security_levels(trust_level)

        permission_list = []
        for sec_level in authorized_asset_security_levels:
            permission_name = PermissionBySecurityLevel.get_name(sec_level)
            permission = await self.__auth_repository.find_permission_by_name(permission_name)
            if permission is not None:
                permission_list.append(permission)
        return permission_list

    async def __assign_permission_to_connector(self, connector: Connector) -> None:
        subject_permission_list = await self.__list_permission_to_trust_level(connector.trust)
        for permission in subject_permission_list:
            new_permission = permission.model_copy(deep=True)

            new_permission.clients.append(connector.id)

            try:
                await self.__auth_repository.save_permission(new_permission)
            except Exception as exc:
                self.__handle_error(
                    description=f"Failed to save the permission [{new_permission.name}] to connector [{connector.id}]",
                    error=exc,
                )

    async def __unassign_permission_to_connector(self, connector: Connector) -> None:
        subject_permission_list = await self.__list_permission_to_trust_level(connector.trust)
        for permission in subject_permission_list:
            new_permission = permission.model_copy(deep=True)

            new_permission.clients = [client_id for client_id in permission.clients if client_id != connector.id]

            try:
                await self.__auth_repository.save_permission(new_permission)
            except Exception as exc:
                self.__handle_error(
                    description=f"Failed to save the permission [{new_permission.name}] to connector [{connector.id}]",
                    error=exc,
                )

    async def __update_permission_to_connector(self, old_connector: Connector, new_connector: Connector) -> None:
        old_trust_value = old_connector.trust.to_number()
        new_trust_value = new_connector.trust.to_number()

        if old_trust_value < new_trust_value:
            await self.__assign_permission_to_connector(new_connector)
        elif old_trust_value > new_trust_value:
            await self.__unassign_permission_to_connector(old_connector)
            await self.__assign_permission_to_connector(new_connector)
        return

    async def create_connector(self, new_connector: ConnectorCreateDto) -> ConnectorDto:
        if await self.__connector_repository.find_by_id(ConnectorId(value=new_connector.id)):
            self.__handle_error(
                status_code=status.HTTP_409_CONFLICT,
                description=f"Connector [{new_connector.id}] is already registered",
            )

        new_connector_entity = Connector(
            id=ConnectorId(value=new_connector.id),
            url=new_connector.url,
            trust=ConnectorTrustLevel(value=new_connector.trust),
        )
        try:
            created_connector = await self.__connector_repository.save(new_connector_entity)
            await self.__assign_permission_to_connector(created_connector)
        except Exception as exc:
            self.__handle_error(description="Failed to create a new connector", error=exc)

        return ConnectorDto.from_entity(created_connector)

    async def update_connector(self, connector_id: str, new_connector: ConnectorUpdateDto) -> None:
        old_connector = await self.__connector_repository.find_by_id(ConnectorId(value=connector_id))

        if old_connector is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Connector ID [{connector_id}] not found"
            )
        if connector_id != new_connector.id:
            self.__handle_error(status_code=status.HTTP_400_BAD_REQUEST, description="Invalid connector update request")

        new_connector_dto = ConnectorDto.model_validate(new_connector, from_attributes=True)
        new_connector_entity = new_connector_dto.to_entity()

        try:
            created_connector = await self.__connector_repository.save(new_connector_entity)
            await self.__update_permission_to_connector(old_connector, created_connector)
        except Exception as exc:
            self.__handle_error(description=f"Failed to update the connector [{connector_id}]", error=exc)

    async def delete_connector(self, connector_id: str) -> None:
        connector = await self.__connector_repository.find_by_id(ConnectorId(value=connector_id))

        if connector is None:
            return
        try:
            await self.__connector_repository.delete(connector.id)
            await self.__unassign_permission_to_connector(connector)
        except Exception as exc:
            self.__handle_error(description=f"Failed to delete the connector [{connector_id}]", error=exc)
