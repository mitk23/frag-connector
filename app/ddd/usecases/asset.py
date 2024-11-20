import httpx
from core.exceptions import ConnectorException
from ddd.domains import domain_service
from ddd.domains.asset import Asset, AssetId, AssetRepositoryIF
from ddd.domains.authorization import AuthRepositoryIF, PermissionBySecurityLevel
from ddd.domains.connector import ConnectorId, ConnectorRepositoryIF
from fastapi import status

from .schemas.asset import AssetCatalogDto, AssetCreateDto, AssetDto, AssetUpdateDto, DistributionContentDto


class AssetQueryUsecase:
    def __init__(self, asset_repository: AssetRepositoryIF):
        self.__asset_repository = asset_repository

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_assets(self) -> dict[str, AssetDto]:
        assets = await self.__asset_repository.find_all()
        return {str(_id): AssetDto.from_entity(asset) for _id, asset in assets.items()}

    async def get_asset(self, asset_id: str) -> AssetDto:
        asset = await self.__asset_repository.find_by_id(AssetId(value=asset_id))
        if asset is None:
            self.__handle_error(status_code=status.HTTP_404_NOT_FOUND, description=f"Asset [{asset_id}] not found")
        return AssetDto.from_entity(asset)


class AssetCommandUsecase:
    def __init__(
        self,
        asset_repository: AssetRepositoryIF,
        connector_repository: ConnectorRepositoryIF,
        auth_repository: AuthRepositoryIF,
    ):
        self.__asset_repository = asset_repository
        self.__connector_repository = connector_repository
        self.__auth_repository = auth_repository

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def __create_asset_permission(self, asset: Asset) -> None:
        asset_security_level = asset.usage_policy.security_level

        subject_resources: list[AssetId] = [asset.id]
        subject_clients: list[ConnectorId] = []

        # resources associated with the same level permission
        permission_name = PermissionBySecurityLevel.get_name(asset_security_level)
        permission_existed = await self.__auth_repository.find_permission_by_name(permission_name)
        if permission_existed is not None:
            subject_resources += permission_existed.resources

        # clients with enough trust level to access the asset
        connectors = await self.__connector_repository.find_all()
        for connector_id, connector in connectors.items():
            if domain_service.check_asset_access_authority_by_level(
                asset_security_level=asset_security_level, connector_trust_level=connector.trust
            ):
                subject_clients.append(connector_id)

        # create security-level permission in common format
        permission = PermissionBySecurityLevel.generate(
            security_level=asset.usage_policy.security_level,
            resources=subject_resources,
            clients=subject_clients,
        )
        try:
            await self.__auth_repository.save_permission(permission)
        except Exception as exc:
            self.__handle_error(description="Failed to create a permission of the asset", error=exc)

    async def __delete_asset_permission(self, asset_id: str) -> None:
        asset_permission = await self.__auth_repository.find_permission_by_resource_id(AssetId(value=asset_id))

        # after deleting asset from keycloak, it also excluded from the resources in permission
        if asset_permission is None:
            return

        asset_permission.resources = [rs_id for rs_id in asset_permission.resources if str(rs_id) != asset_id]
        if len(asset_permission.resources) == 0:
            # when the permission associates no resources
            await self.__auth_repository.delete_permission(asset_permission.id)
        else:
            await self.__auth_repository.save_permission(asset_permission)

    async def __update_asset_permission(self, asset: Asset) -> None:
        # 1: remove the asset from resources in the previous permission
        await self.__delete_asset_permission(str(asset.id))
        # 2: associate the asset with a new permission
        await self.__create_asset_permission(asset)

    async def create_asset(self, new_asset: AssetCreateDto) -> AssetDto:
        # check asset title duplication
        assets = await self.__asset_repository.find_all()
        for asset in assets.values():
            if asset.title == new_asset.title:
                self.__handle_error(
                    status_code=status.HTTP_409_CONFLICT, description=f"Asset [{new_asset.title}] is already existed"
                )

        new_asset_entity = Asset(
            id=None,
            title=new_asset.title,
            description=new_asset.description,
            usage_policy=new_asset.usage_policy.to_entity() if new_asset.usage_policy else None,
            distributions=[distribution.to_entity() for distribution in new_asset.distributions],
            vectors=new_asset.vectors.to_entity() if new_asset.vectors else None,
        )
        try:
            # TODO: transaction
            created_asset = await self.__asset_repository.save(new_asset_entity)
            await self.__create_asset_permission(created_asset)
        except Exception as exc:
            self.__handle_error(description="Failed to create a new asset", error=exc)

        return AssetDto.from_entity(created_asset)

    async def update_asset(self, asset_id: str, new_asset: AssetUpdateDto) -> None:
        if asset_id != new_asset.id:
            self.__handle_error(status_code=status.HTTP_400_BAD_REQUEST, description="Invalid asset ID in payload")

        old_asset = await self.__asset_repository.find_by_id(AssetId(value=asset_id))
        if old_asset is None:
            self.__handle_error(status_code=status.HTTP_404_NOT_FOUND, description=f"Asset [{asset_id}] not found")

        new_asset_entity = AssetDto.model_validate(new_asset.model_dump()).to_entity()
        try:
            # TODO: transaction
            await self.__asset_repository.save(new_asset_entity)
            await self.__update_asset_permission(new_asset_entity)
        except Exception as exc:
            self.__handle_error(description=f"Failed to update the asset [{asset_id}]", error=exc)

    async def delete_asset(self, asset_id: str) -> None:
        try:
            # TODO: transaction
            await self.__asset_repository.delete(AssetId(value=asset_id))
            await self.__delete_asset_permission(asset_id)
        except Exception as exc:
            self.__handle_error(description=f"Failed to delete the asset [{asset_id}]", error=exc)


class AssetCatalogUsecase:
    def __init__(
        self, asset_repository: AssetRepositoryIF, auth_repository: AuthRepositoryIF, catalog_access_token: str
    ):
        self.__asset_repository = asset_repository
        self.__auth_repository = auth_repository
        self.__catalog_access_token = catalog_access_token

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_asset_catalogs(self) -> dict[str, AssetCatalogDto]:
        assets = await self.__asset_repository.find_all()

        authorized_asset_id_set = await self.__auth_repository.authorized_resources(
            self.__catalog_access_token, list(assets.keys())
        )
        authorized_asset_catalogs = {
            str(_id): AssetCatalogDto.from_entity(asset)
            for _id, asset in assets.items()
            if _id in authorized_asset_id_set
        }
        return authorized_asset_catalogs

    async def get_asset_catalog(self, asset_id: str) -> AssetCatalogDto:
        asset = await self.__asset_repository.find_by_id(AssetId(value=asset_id))
        if asset is None:
            self.__handle_error(status_code=status.HTTP_404_NOT_FOUND, description=f"Asset [{asset_id}] not found")

        is_authorized = await self.__auth_repository.authorize(self.__catalog_access_token, asset)
        if not is_authorized:
            self.__handle_error(
                status_code=status.HTTP_403_FORBIDDEN,
                description=f"Denied access to asset [{asset_id}]. You don't have permission.",
            )

        return AssetCatalogDto.from_entity(asset)

    async def download_distribution(self, asset_id: str, distribution_title: str) -> DistributionContentDto:
        asset = await self.__asset_repository.find_by_id(AssetId(value=asset_id))

        is_authorized = await self.__auth_repository.authorize(self.__catalog_access_token, asset)
        if not is_authorized:
            self.__handle_error(
                status_code=status.HTTP_403_FORBIDDEN,
                description=f"Denied access to asset [{asset_id}]. You don't have permission.",
            )

        distribution = None
        for distrib in asset.distributions:
            if distrib.title == distribution_title:
                distribution = distrib

        if distribution is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Distribution [{distribution_title}] not found"
            )
        if distribution.url is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Distribution [{distribution_title}] URL not found"
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(str(distribution.url))
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(description=f"Error while requesting {err.request.url!r}", error=err)
            except httpx.HTTPStatusError as err:
                self.__handle_error(description=f"Error on fetching the distribution: {err.request.url!r}", error=err)

        return DistributionContentDto(
            media_type=distribution.media_type,
            content=response.content,
        )
