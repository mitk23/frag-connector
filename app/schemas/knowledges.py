import textwrap
from typing import Any, Literal

from pydantic import BaseModel, Field


class KnowledgeQueryRequestConfig(BaseModel):
    top_k: int | None = Field(default=3, description="各データ提供者から取得する文書数", examples=[5])
    include_embedding: bool | None = Field(
        default=True, description="レスポンスに埋め込みを含むかどうか", examples=[True]
    )
    filter: dict[str, Any] | None = Field(
        default=None,
        description="各データ提供者によるベクトル検索時のフィルタ（ベクトルDBに依存）",
        examples=[{"tag": "example-tag"}],
    )
    exact_search: bool | None = Field(
        default=False, description="ベクトル検索（最近傍探索）に近似を利用するかどうか", examples=[False]
    )


class KnowledgeQueryRequest(BaseModel):
    embedding: list[float] = Field(description="クエリテキストの埋め込みベクトル", examples=[[0.1, 0.2, 0.3]])
    config: KnowledgeQueryRequestConfig | None = Field(
        default=KnowledgeQueryRequestConfig(), description="各データ提供者に対する検索リクエストのパラメータ"
    )


class KnowledgeResponse(BaseModel):
    id: str = Field(description="ベクトルDB上で割り当てられたベクトルID", examples=["42"])
    text: str = Field(description="関連文書のテキスト", examples=["This is an example text."])
    embedding: list[float] | None = Field(
        default=None, description="関連文書の埋め込みベクトル", examples=[[0.1, 0.2, 0.3]]
    )
    score: float = Field(description="文書の埋め込みベクトルとクエリベクトルの類似度", examples=[0.88])
    metadata: dict[str, Any] | None = Field(
        default=None, description="ベクトルDB上で設定されたベクトルのメタデータ", examples=[{"tag": "example-tag"}]
    )


class FederatedKnowledgeResponse(KnowledgeResponse):
    provider: str = Field(description="関連文書を提供したデータ提供者ID", examples=["example-connector-1"])


class FederatedKnowledgeQueryRequest(BaseModel):
    query: KnowledgeQueryRequest = Field(description="関連文書の検索クエリ")
    providers: list[str] = Field(
        description="関連文書検索を依頼するデータ提供者のID列",
        examples=[["example-connector-1", "example-connector-2", "example-connector-10"]],
    )
    knowledge_rerank_method: Literal["naive", "cosine"] | None = Field(
        default="naive",
        description=textwrap.dedent("""
            各データ提供者から取得した関連文書の集約方法
            - `naive`: 類似度スコアによるソート
            - `cosine`: 返却された埋め込みベクトルを用いてコサイン類似度を再計算）
        """),
        examples=["naive"],
    )
    return_num_knowledges: int | None = Field(default=5, description="コネクタから返却する関連文書数", examples=[10])
