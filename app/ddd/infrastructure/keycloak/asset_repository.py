from core.exceptions import InternalException
from ddd.domains.asset import Asset, AssetId, AssetRepositoryIF
from ddd.domains.authorization import AuthConfig
from ddd.infrastructure.json.asset_repository import JSONAssetRepository
from keycloak import KeycloakOpenIDConnection, KeycloakUMA
from keycloak.exceptions import KeycloakDeleteError, KeycloakGetError, KeycloakPostError, KeycloakPutError

from .asset_model import AssetKeycloakDao


class KeycloakAssetRepository(AssetRepositoryIF):
    def __init__(self, config: AuthConfig):
        self.__server_url = config.server_url
        self.__realm_name = config.realm_name
        self.__username = config.username
        self.__password = config.password
        self.__client_id = config.client_id
        self.__client_secret = config.client_secret
        self.__grant_type = config.grant_type

        self.__connection = KeycloakOpenIDConnection(
            server_url=self.__server_url,
            realm_name=self.__realm_name,
            client_id=self.__client_id,
            client_secret_key=self.__client_secret,
        )

        self.openid_client = self.__connection.keycloak_openid
        self.uma_client = KeycloakUMA(self.__connection)

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)

    async def find_all(self) -> dict[AssetId, Asset]:
        resource_list = await self.uma_client.a_resource_set_list()
        resource_dao_list = [AssetKeycloakDao.model_validate(rs) for rs in resource_list]
        resource_entity_list = [rs_dao.to_entity() for rs_dao in resource_dao_list]
        return {asset.id: asset for asset in resource_entity_list}

    async def find_by_id(self, _id: AssetId) -> Asset | None:
        _id_str = str(_id)
        try:
            resource = await self.uma_client.a_resource_set_read(_id_str)
        except KeycloakGetError:
            return None
        return AssetKeycloakDao.model_validate(resource).to_entity()

    async def save(self, asset: Asset) -> Asset:
        asset_dao = AssetKeycloakDao.from_entity(asset)

        if asset_dao.id is not None:
            try:
                await self.uma_client.a_resource_set_update(
                    asset_dao.id, asset_dao.model_dump(exclude="id", exclude_none=True)
                )
            except KeycloakPutError as err:
                self.__handle_error(error=err, description=f"Failed to update the resource {asset_dao.id} on Keycloak")
            return asset

        # resources_with_same_name = self.uma_client.a_resource_set_list_ids(name=asset_dao.name, exact_name=True)
        # if len(resources_with_same_name) > 0:
        #     self.__handle_error(description=f"Resource `{asset_dao.name}` is already existed")

        try:
            _created_asset = await self.uma_client.a_resource_set_create(asset_dao.model_dump(exclude_none=True))
        except KeycloakPostError as err:
            self.__handle_error(error=err, description="Failed to create a new resource on Keycloak")

        # attriutes are not included in Keyclok post response
        # --> re-query to get resource attributes
        _created_asset_id = AssetKeycloakDao.model_validate(_created_asset).to_entity().id
        created_asset = await self.find_by_id(_created_asset_id)
        return created_asset

    async def delete(self, _id: AssetId) -> None:
        try:
            await self.uma_client.a_resource_set_delete(str(_id))
        except KeycloakDeleteError:
            return


class JSONandKeycloakAssetRepository(AssetRepositoryIF):
    def __init__(self, json_config_path: str, auth_config: AuthConfig):
        self.__json_repository = JSONAssetRepository(json_config_path)
        self.__kc_repository = KeycloakAssetRepository(auth_config)

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)

    async def find_all(self) -> dict[AssetId, Asset]:
        return await self.__json_repository.find_all()

    async def find_by_id(self, _id: AssetId) -> Asset | None:
        return await self.__json_repository.find_by_id(_id)

    async def save(self, asset: Asset) -> Asset:
        try:
            kc_asset = await self.__kc_repository.save(asset)
            try:
                created_asset = await self.__json_repository.save(kc_asset)
            except InternalException as exc:
                self.__handle_error(description="Failed to create a new asset on JSON", error=exc)
        except InternalException as exc:
            self.__handle_error(description="Failed to create a new asset on Keycloak", error=exc)
        return created_asset

    async def delete(self, _id: AssetId) -> None:
        await self.__kc_repository.delete(_id)
        await self.__json_repository.delete(_id)
