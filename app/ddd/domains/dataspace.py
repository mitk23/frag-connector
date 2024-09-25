import abc
from typing import Any

from ddd.domains.asset import AssetCatalog, AssetId
from ddd.domains.connector import ConnectorId
from ddd.domains.knowledge import Knowledge, KnowledgeQuery


class DataspaceAssetQueryServiceIF(abc.ABC):
    @abc.abstractmethod
    async def find_all(self, provider_id: ConnectorId) -> dict[AssetId, AssetCatalog]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(self, provider_id: ConnectorId, asset_id: AssetId) -> AssetCatalog | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def pull(self, provider_id: ConnectorId, asset_id: AssetId) -> dict[str, Any]:
        raise NotImplementedError


class DataspaceKnowledgeQueryServiceIF(abc.ABC):
    @abc.abstractmethod
    async def query(self, provider_id: ConnectorId, query: KnowledgeQuery) -> list[Knowledge]:
        raise NotImplementedError

    # @abc.abstractmethod
    # async def query_llm(self):
    #     raise NotImplementedError
