from typing import Literal

from .base import BaseApiSchema


class ConnectorBase(BaseApiSchema):
    id: str
    url: str
    trust: Literal["low", "medium", "high"] | None = "low"


class ConnectorCreateRequest(ConnectorBase):
    pass


class ConnectorUpdateRequest(ConnectorBase):
    pass


class ConnectorResponse(ConnectorBase):
    pass
