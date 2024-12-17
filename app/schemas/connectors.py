import textwrap
from typing import Literal

from pydantic import Field

from .base import BaseApiSchema


class ConnectorBase(BaseApiSchema):
    id: str = Field(description="コネクタID（OAuth 2.0におけるClientID）", examples=["example-connector"])
    url: str = Field(description="コネクタAPIのベースURL", examples=["http://connector.example.com:8000/"])
    trust: Literal["low", "medium", "high"] | None = Field(
        default="low",
        description=textwrap.dedent("""
            コネクタの信頼レベルを以下の3段階で指定する
            - `high`: 任意の機密レベルのアセットにアクセス可能
            - `medium`: 機密レベル`public`または`restricted`のアセットにのみアクセス可能
            - `low`: 機密レベル`public`のアセットにのみアクセス可能
        """),
        examples=["low"],
    )


class ConnectorCreateRequest(ConnectorBase):
    pass


class ConnectorUpdateRequest(ConnectorBase):
    pass


class ConnectorResponse(ConnectorBase):
    pass
