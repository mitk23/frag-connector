from core.exceptions import InternalException
from ddd.domains.asset import Asset, AssetId
from ddd.domains.authorization import AuthConfig, AuthRepositoryIF, Permission
from keycloak import KeycloakOpenIDConnection, KeycloakUMA
from keycloak.exceptions import KeycloakDeleteError, KeycloakGetError, KeycloakPostError, KeycloakPutError
from keycloak.uma_permissions import AuthStatus

from .authorization_model import PermissionKeycloakDao


class KeycloakAuthRepository(AuthRepositoryIF):
    def __init__(self, config: AuthConfig):
        self.server_url = config.server_url
        self.realm_name = config.realm_name
        self.username = config.username
        self.password = config.password
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.grant_type = config.grant_type

        self.__connection = KeycloakOpenIDConnection(
            server_url=self.server_url,
            realm_name=self.realm_name,
            client_id=self.client_id,
            client_secret_key=self.client_secret,
        )

        self.openid_client = self.__connection.keycloak_openid
        self.uma_client = KeycloakUMA(self.__connection)

    def __handle_error(self, description: str, error: Exception | None = None):
        raise InternalException(description=description, upstream_exc=error)

    async def __is_my_token(self, token: str) -> bool:
        if not await self.verify_authenticity(token):
            return False

        my_base_url: str = self.openid_client._connection.base_url
        my_realm: str = self.openid_client._realm_name
        my_iss = f"{my_base_url}/realms/{my_realm}"

        token_info: dict = await self.openid_client.a_decode_token(token)

        is_same_client: bool = token_info.get("azp") == self.openid_client._client_id
        is_same_iss: bool = token_info.get("iss") == my_iss

        return is_same_client and is_same_iss

    async def __find_resources_associated_with_permission(self, permission_id: str) -> list[str]:
        resources_all = self.uma_client.a_resource_set_list()

        associated_resource_list = []
        async for resource in resources_all:
            rs_id = resource.get("_id")
            try:
                rs_permission_list = await self.uma_client.a_policy_query(resource=rs_id, first=0, maximum=1)
            except KeycloakGetError as err:
                self.__handle_error(
                    error=err, description=f"Failed to get permissions of the resource [{rs_id}] from Keycloak)"
                )
            if len(rs_permission_list) == 0:
                continue
            if rs_permission_list[0].get("id") == permission_id:
                associated_resource_list.append(rs_id)
        return associated_resource_list

    async def __update(self, permission: PermissionKeycloakDao) -> None:
        permission_dict = permission.model_dump(exclude_none=True)
        try:
            await self.uma_client.a_policy_update(permission.id, permission_dict)
        except KeycloakPutError as err:
            self.__handle_error(
                description=f"Failed to update the permission [{permission.name}] on Keycloak", error=err
            )

    async def __create(self, permission: PermissionKeycloakDao) -> Permission:
        permission_dict = permission.model_dump(exclude_none=True)

        subject_resource_id = permission.resources[0]
        try:
            saved_permission = await self.uma_client.a_policy_resource_create(subject_resource_id, permission_dict)
        except KeycloakPostError as err:
            self.__handle_error(error=err, description="Failed to create a new permission on Keycloak")

        # resources claim is not included in keycloak response
        saved_permission_dao = PermissionKeycloakDao.model_validate(saved_permission)
        saved_permission_dao.resources = permission.resources

        return saved_permission_dao.to_entity()

    async def authenticate(self) -> str:
        token_response = await self.openid_client.a_token(grant_type=self.grant_type)
        token: str = token_response.get("access_token")
        return token

    async def verify_authenticity(self, token: str) -> bool:
        token_info = await self.openid_client.a_introspect(token=token)
        is_active: bool = token_info.get("active", False)
        return is_active

    async def authorize(self, token: str, resource: Asset) -> bool:
        # allow access to my resources (because keycloak does not support this behavior)
        if await self.__is_my_token(token):
            return True

        resource_name = resource.title
        auth_status: AuthStatus = await self.openid_client.a_has_uma_access(token, resource_name)
        return auth_status.is_authorized

    async def authorized_resources(self, token: str, resource_id_list: list[AssetId]) -> set[AssetId]:
        if await self.__is_my_token(token):
            return set(resource_id_list)

        try:
            authorized_resource_list: list[dict[str, str]] = await self.openid_client.a_uma_permissions(
                token, [str(rs_id) for rs_id in resource_id_list]
            )
        except KeycloakPostError as err:
            self.__handle_error(description="Failed to get permissions from keycloak", error=err)

        authorized_resource_id_list = [AssetId(value=rs_dict.get("rsid")) for rs_dict in authorized_resource_list]
        return set(authorized_resource_id_list)

    async def find_permission_by_id(self, permission_id: str) -> Permission | None:
        raise NotImplementedError

    async def find_permission_by_name(self, permission_name: str) -> Permission | None:
        try:
            permission_list = await self.uma_client.a_policy_query(name=permission_name, first=0, maximum=1)
        except KeycloakGetError as err:
            self.__handle_error(
                description=f"Failed to get the permission [{permission_name}] from Keycloak", error=err
            )

        if len(permission_list) == 0:
            return None
        permission_dao = PermissionKeycloakDao.model_validate(permission_list[0])

        # find resources associated with this permission as well
        # since policy query response from Keycloak does not include resources,
        associated_resource_list = await self.__find_resources_associated_with_permission(permission_dao.id)
        permission_dao.resources = associated_resource_list

        return permission_dao.to_entity()

    async def find_permission_by_resource_id(self, resource_id: AssetId) -> Permission | None:
        try:
            permission_list = await self.uma_client.a_policy_query(resource=str(resource_id), first=0, maximum=1)
        except KeycloakGetError as err:
            self.__handle_error(
                error=err, description=f"Failed to get permissions of the resource [{str(resource_id)}] from Keycloak"
            )

        if len(permission_list) == 0:
            return None
        permission_dao = PermissionKeycloakDao.model_validate(permission_list[0])

        # find resources associated with this permission as well
        # since policy query response from Keycloak does not include resources,
        associated_resource_id_list = await self.__find_resources_associated_with_permission(permission_dao.id)
        permission_dao.resources = associated_resource_id_list

        return permission_dao.to_entity()

    async def save_permission(self, permission: Permission) -> Permission:
        permission_dao = PermissionKeycloakDao.from_entity(permission)
        # guarantee self client id is included in permission clients
        permission_dao.clients.append(self.client_id)

        # check if permission with same name is already existed
        permission_existed = await self.find_permission_by_name(permission_dao.name)
        if permission_existed is not None:
            permission_existed_dao = PermissionKeycloakDao.from_entity(permission_existed)
            permission_dao.id = permission_existed_dao.id
            await self.__update(permission_dao)
            return permission

        saved_permission = await self.__create(permission_dao)
        return saved_permission

    async def delete_permission(self, permission_id: str) -> None:
        try:
            await self.uma_client.a_policy_delete(permission_id)
        except KeycloakDeleteError as err:
            self.__handle_error(description="Failed to delete the permission from Keycloak", error=err)
