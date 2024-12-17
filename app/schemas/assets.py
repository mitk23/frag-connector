import textwrap
from typing import Literal

from pydantic import UUID4, BaseModel, Field, HttpUrl

from .base import BaseApiSchema


class DistributionBase(BaseModel):
    title: str = Field(description="配信のタイトル", examples=["example.json"])
    description: str | None = Field(default=None, description="配信の説明", examples=["example description"])
    media_type: str | None = Field(default=None, description="配信のMIMEタイプ", examples=["application/json"])


class DistributionCatalog(DistributionBase):
    pass


class Distribution(DistributionBase):
    url: HttpUrl | None = Field(
        default=None, description="配信のURL", examples=["https://example.com/assets/example.json"]
    )


class VectorFilter(BaseModel):
    has_metadata: dict[str, str | list[str]] | None = Field(
        default={},
        description=textwrap.dedent("""
            メタデータによるベクトルのフィルタ条件をkey-value形式で記述する
            - key: メタデータのタイトル
            - value: 文字列および文字列のリストで指定する（文字列で指定すると一致条件、リストで指定すると包含条件）
        """),
        examples=[{"group": "group-A", "tag": ["example-tag-1", "example-tag-2"]}],
    )
    has_id: set[str] | None = Field(
        default=set(),
        description=textwrap.dedent("""
            IDによるベクトルのフィルタ条件
            - ユニークなID列を指定するか、`*`を指定するとインデックス上の任意のベクトルを表す
        """),
        examples=[["42", "100", "1234", "9999"]],
    )


class AssetUsagePolicy(BaseModel):
    security_level: Literal["confidential", "restricted", "public"] | None = Field(
        default="public",
        description=textwrap.dedent("""
            アセットの機密レベルを以下の3段階で指定する
            - `confidential`: 信頼レベル`high`のコネクタにのみアクセスを許可
            - `restricted`: 信頼レベル`high`または`medium`のコネクタにのみアクセスを許可
            - `public`: 任意の信頼レベルのコネクタにアクセスを許可
        """),
        examples=["public"],
    )


class AssetBase(BaseApiSchema):
    title: str = Field(description="アセットのタイトル", examples=["example-asset"])
    description: str | None = Field(default=None, description="アセットの説明", examples=["example asset"])
    usage_policy: AssetUsagePolicy | None = Field(
        default=AssetUsagePolicy(),
        description="アセットの利用条件（この条件はアセットに含まれるすべての配信およびベクトルに適用される）",
    )


class AssetCatalogResponse(AssetBase):
    id: UUID4 = Field(description="アセットID（UUID4）", examples=["7955ab20-1e0a-4a83-bf79-0bd933792825"])
    distributions: list[DistributionCatalog] = Field(description="アセットに含まれる配信リスト")


class AssetCreateRequest(AssetBase):
    distributions: list[Distribution] | None = Field(default=None, description="アセットに含まれる配信リスト")
    vectors: VectorFilter | None = Field(
        default=None,
        description=textwrap.dedent("""
            アセットに含まれるベクトル集合
            - コネクタがベクトルを提供する場合（文書検索API、連邦型RAG APIなど）のみ設定する
            - アセットの利用条件に紐づけるベクトル集合をフィルタ条件で記述する
        """),
    )


class AssetUpdateRequest(AssetBase):
    id: UUID4 = Field(description="アセットID（UUID4）", examples=["7955ab20-1e0a-4a83-bf79-0bd933792825"])
    distributions: list[Distribution] | None = Field(default=None, description="アセットに含まれる配信リスト")
    vectors: VectorFilter | None = Field(
        default=None,
        description=textwrap.dedent("""
            アセットに含まれるベクトル集合
            - コネクタがベクトルを提供する場合（文書検索API、連邦型RAG APIなど）のみ設定する
            - アセットの利用条件に紐づけるベクトル集合をフィルタ条件で記述する
        """),
    )


class AssetResponse(AssetBase):
    id: UUID4 = Field(description="アセットID（UUID4）", examples=["7955ab20-1e0a-4a83-bf79-0bd933792825"])
    distributions: list[Distribution] | None = Field(default=None, description="アセットに含まれる配信リスト")
    vectors: VectorFilter | None = Field(
        default=None,
        description=textwrap.dedent("""
            アセットに含まれるベクトル集合
            - コネクタがベクトルを提供する場合（文書検索API、連邦型RAG APIなど）のみ設定する
            - アセットの利用条件に紐づけるベクトル集合をフィルタ条件で記述する
        """),
    )
