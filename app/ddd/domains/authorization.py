import abc
from typing import ClassVar, Literal

from core.exceptions import InternalException
from ddd.domains.asset import Asset, AssetId
from ddd.domains.base import ValueObject
from pydantic import BaseModel


class PermissionDecisionStrategy(ValueObject):
    UNANIMOUS: ClassVar[str] = "UNANIMOUS"
    AFFIRMATIVE: ClassVar[str] = "AFFIRMATIVE"
    CONSENSUS: ClassVar[str] = "CONSENSUS"

    value: Literal["UNANIMOUS", "AFFIRMATIVE", "CONSENSUS"]

    @classmethod
    def generate(cls, strategy=None) -> "PermissionDecisionStrategy":
        if strategy is None:
            return cls(value=cls.UNANIMOUS)
        return cls(value=strategy)


class Permission(BaseModel):
    id: str | None
    name: str
    description: str | None = None
    resources: list[AssetId] | None = []
    policies: list[str] | None = []
    clients: list[str] | None = []
    groups: list[str] | None = []
    roles: list[str] | None = []
    users: list[str] | None = []
    decision_strategy: PermissionDecisionStrategy | None = PermissionDecisionStrategy.generate()


class AuthConfig(BaseModel):
    server_url: str | None = None
    realm_name: str | None = None
    username: str | None = None
    password: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    grant_type: str | None = None


class AuthRepositoryIF(abc.ABC):
    def __init__(self, config: AuthConfig):
        self.server_url = config.server_url
        self.realm_name = config.realm_name
        self.username = config.username
        self.password = config.password
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.grant_type = config.grant_type

    @abc.abstractmethod
    async def authenticate(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def verify_authenticity(self, token: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def authorize(self, token: str, asset: Asset) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def authorized_resources(self, token: str, resource_id_list: list[AssetId]) -> set[AssetId]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_permission_by_id(self, permission_id: str) -> Permission | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_permission_by_name(self, permission_name: str) -> Permission | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_permission_by_resource_id(self, resource_id: AssetId) -> Permission | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def save_permission(self, permission: Permission) -> Permission:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_permission(self, permission_id: str) -> None:
        raise NotImplementedError

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)
