import abc
from typing import ClassVar, Literal

from ddd.domains.asset import Asset, AssetId, AssetSecurityLevel
from ddd.domains.base import ValueObject
from ddd.domains.connector import ConnectorId
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
    clients: list[ConnectorId] | None = []
    groups: list[str] | None = []
    roles: list[str] | None = []
    users: list[str] | None = []
    decision_strategy: PermissionDecisionStrategy | None = PermissionDecisionStrategy(
        value=PermissionDecisionStrategy.UNANIMOUS
    )


class PermissionBySecurityLevel(Permission):
    decision_strategy: PermissionDecisionStrategy | None = PermissionDecisionStrategy(
        value=PermissionDecisionStrategy.AFFIRMATIVE
    )

    @staticmethod
    def get_name(security_level: AssetSecurityLevel) -> str:
        return f"permission-{str(security_level)}"

    @staticmethod
    def get_description(security_level: AssetSecurityLevel) -> str:
        return f"Permission for {str(security_level)} resources"

    @staticmethod
    def generate(
        security_level: AssetSecurityLevel, resources: list[AssetId], clients: list[ConnectorId]
    ) -> "PermissionBySecurityLevel":
        return PermissionBySecurityLevel(
            id=None,
            name=PermissionBySecurityLevel.get_name(security_level),
            description=PermissionBySecurityLevel.get_description(security_level),
            resources=resources,
            clients=clients,
        )


class AuthConfig(BaseModel):
    server_url: str | None = None
    realm_name: str | None = None
    username: str | None = None
    password: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    grant_type: str | None = None


class AuthRepositoryIF(abc.ABC):
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
