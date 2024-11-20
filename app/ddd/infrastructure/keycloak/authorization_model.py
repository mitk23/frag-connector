from ddd.domains.asset import AssetId
from ddd.domains.authorization import Permission, PermissionDecisionStrategy
from ddd.domains.connector import ConnectorId
from pydantic import BaseModel


class PermissionKeycloakDao(BaseModel):
    id: str | None
    name: str
    description: str | None = None
    type: str | None = None
    scopes: list[str] | None = None
    logic: str | None = None
    decisionStrategy: str | None = None
    owner: str | None = None
    resources: list[str] | None = []
    clients: list[str] | None = []
    groups: list[str] | None = []
    roles: list[str] | None = []
    users: list[str] | None = []
    condition: str | None = None

    def to_entity(self) -> Permission:
        return Permission(
            id=self.id,
            name=self.name,
            description=self.description,
            decision_strategy=PermissionDecisionStrategy.generate(self.decisionStrategy),
            resources=[AssetId(value=rs_id) for rs_id in self.resources],
            clients=[ConnectorId(value=client_id) for client_id in self.clients],
            groups=self.groups,
            roles=self.roles,
            users=self.users,
        )

    @staticmethod
    def from_entity(permission: Permission) -> "PermissionKeycloakDao":
        return PermissionKeycloakDao(
            id=permission.id,
            name=permission.name,
            description=permission.description,
            decisionStrategy=str(permission.decision_strategy),
            resources=[str(rs_id) for rs_id in permission.resources],
            clients=[str(client_id) for client_id in permission.clients],
            groups=permission.groups,
            roles=permission.roles,
            users=permission.users,
        )
