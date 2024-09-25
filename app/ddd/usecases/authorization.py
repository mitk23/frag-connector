from core.exceptions import ConnectorException
from ddd.domains.asset import AssetId, AssetSecurityLevel
from ddd.domains.authorization import AuthRepositoryIF, Permission, PermissionDecisionStrategy
from ddd.domains.connector import ConnectorTrustLevel
from ddd.usecases.connector import ConnectorUsecase
from fastapi import status

from .schemas.asset import AssetDto
from .schemas.authorization import PermissionDto


class AuthorizationUsecase:
    def __init__(self, auth_repository: AuthRepositoryIF, connector_usecase: ConnectorUsecase):
        self.__auth_repository = auth_repository
        self.__connector_usecase = connector_usecase

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def __read_permission_by_name(self, permission_name: str) -> PermissionDto | None:
        permission = await self.__auth_repository.find_permission_by_name(permission_name)
        if permission is None:
            return None
        return PermissionDto.from_entity(permission)

    async def __find_assets_associated_with_permission(self, permission_name: str) -> list[str]:
        permission_dto = await self.__read_permission_by_name(permission_name)
        if permission_dto is None:
            return []
        return permission_dto.resources

    async def __confidential_permission(self, asset_id: str, clients: list[str]) -> Permission:
        permission_name = f"permission-{AssetSecurityLevel.CONFIDENTIAL}"

        resources = await self.__find_assets_associated_with_permission(permission_name)
        resources.append(asset_id)

        return Permission(
            id=None,
            name=permission_name,
            description="Permission for confidential documents",
            resources=[AssetId(value=rs_id) for rs_id in resources],
            clients=clients,
            decision_strategy=PermissionDecisionStrategy.generate(PermissionDecisionStrategy.AFFIRMATIVE),
        )

    async def __restricted_permission(self, asset_id: str, clients: list[str]) -> Permission:
        permission_name = f"permission-{AssetSecurityLevel.RESTRICTED}"

        resources = await self.__find_assets_associated_with_permission(permission_name)
        resources.append(asset_id)

        return Permission(
            id=None,
            name=permission_name,
            description="Permission for restricted documents",
            resources=[AssetId(value=rs_id) for rs_id in resources],
            clients=clients,
            decision_strategy=PermissionDecisionStrategy.generate(PermissionDecisionStrategy.AFFIRMATIVE),
        )

    async def __public_permission(self, asset_id: str, clients: list[str]) -> Permission:
        permission_name = f"permission-{AssetSecurityLevel.PUBLIC}"

        resources = await self.__find_assets_associated_with_permission(permission_name)
        resources.append(asset_id)

        return Permission(
            id=None,
            name=permission_name,
            description="Permission for public documents",
            resources=[AssetId(value=rs_id) for rs_id in resources],
            clients=clients,
            decision_strategy=PermissionDecisionStrategy.generate(PermissionDecisionStrategy.AFFIRMATIVE),
        )
        # return Permission(
        #     id=None,
        #     name=AssetSecurityLevel.PUBLIC,
        #     description="Permission for public documents",
        #     resources=[AssetId(value=rs_id) for rs_id in resources],
        #     policies=["Default Policy"],
        # )

    async def __create_asset_permission_by_security_level(
        self, asset_id: str, asset_security_level: str
    ) -> PermissionDto:
        if asset_security_level == AssetSecurityLevel.CONFIDENTIAL:
            # connectorから信頼レベルを取り出して、policyを作成する
            connectors_with_trust = await self.__connector_usecase.list_connectors_by_trust_level(
                ConnectorTrustLevel.HIGH
            )
            connector_name_list = [conn.name for conn in connectors_with_trust.values()]
            permission = await self.__confidential_permission(asset_id, connector_name_list)
        elif asset_security_level == AssetSecurityLevel.RESTRICTED:
            connectors_with_trust = await self.__connector_usecase.list_connectors_by_trust_level(
                ConnectorTrustLevel.MEDIUM
            )
            connector_name_list = [conn.name for conn in connectors_with_trust.values()]
            permission = await self.__restricted_permission(asset_id, connector_name_list)
        elif asset_security_level == AssetSecurityLevel.PUBLIC:
            connectors_with_trust = await self.__connector_usecase.list_connectors_by_trust_level(
                ConnectorTrustLevel.LOW
            )
            connector_name_list = [conn.name for conn in connectors_with_trust.values()]
            permission = await self.__public_permission(asset_id, connector_name_list)
        else:
            self.__handle_error(description="Asset security level must be specified")

        created_permission = await self.__auth_repository.save_permission(permission)
        return PermissionDto.from_entity(created_permission)

    async def get_token(self) -> str:
        return await self.__auth_repository.authenticate()

    async def verify_token(self, token: str) -> bool:
        return await self.__auth_repository.verify_authenticity(token)

    async def authorize(self, token: str, asset: AssetDto) -> bool:
        return await self.__auth_repository.authorize(token, asset.to_entity())

    async def authorized_resources(self, token: str, asset_id_list: list[str]) -> set[str]:
        _asset_id_list = [AssetId(value=_id) for _id in asset_id_list]

        authorized_asset_id_list = await self.__auth_repository.authorized_resources(token, _asset_id_list)
        return set(str(_id) for _id in authorized_asset_id_list)

    async def read_permission(self, permission_name: str) -> PermissionDto:
        """
        get a permission information by its name
        """
        permission_dto = await self.__read_permission_by_name(permission_name)
        if permission_dto is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Permission `{permission_name}` not found"
            )
        return permission_dto

    async def find_asset_permission(self, asset_id: str) -> PermissionDto:
        """
        find a permission associated with the asset
        """
        permission = await self.__auth_repository.find_permission_by_resource_id(AssetId(value=asset_id))
        if permission is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND,
                description=f"Permission associated with the resource `{asset_id}` not found",
            )
        return PermissionDto.from_entity(permission)

    async def create_asset_permission(
        self, asset_id: str, asset_security_level: str | None = None, permission: PermissionDto | None = None
    ) -> PermissionDto:
        """
        newly create a new permission associated with the asset by security level
        """
        if permission is None:
            if asset_security_level is None:
                self.__handle_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    description="must specify asset's security level or permission",
                )
            # permission by asset's security level
            return await self.__create_asset_permission_by_security_level(asset_id, asset_security_level)

        permission_entity = permission.to_entity()
        created_permission = await self.__auth_repository.save_permission(permission_entity)
        return PermissionDto.from_entity(created_permission)

    async def update_asset_permission(self, asset_id: str, asset_security_level: str) -> None:
        """
        associate the asset with a new security level permission
        """
        # 1. remove asset from resources in the permission associated with the asset
        await self.delete_asset_permission(asset_id)
        # 2. associate the asset with a new permission
        await self.create_asset_permission(asset_id, asset_security_level)

    async def delete_asset_permission(self, asset_id: str):
        """
        delete the association between asset and permission
        """
        asset_permission_dto = await self.find_asset_permission(asset_id)

        new_permission_resources = [rs_id for rs_id in asset_permission_dto.resources if rs_id != asset_id]
        asset_permission_dto.resources = new_permission_resources

        await self.__auth_repository.save_permission(asset_permission_dto.to_entity())
