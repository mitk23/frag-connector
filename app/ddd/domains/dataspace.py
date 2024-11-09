import abc

from ddd.domains.asset import AssetCatalog, AssetId, DistributionContent
from ddd.domains.connector import ConnectorId
from ddd.domains.knowledge import Knowledge, KnowledgeQuery


class DataspaceAssetCatalogQueryServiceIF(abc.ABC):
    @abc.abstractmethod
    async def find_all(self, provider_id: ConnectorId) -> dict[AssetId, AssetCatalog]:
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(self, provider_id: ConnectorId, asset_id: AssetId) -> AssetCatalog | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def download(
        self, provider_id: ConnectorId, asset_id: AssetId, distribution_title: str
    ) -> DistributionContent:
        raise NotImplementedError


class DataspaceKnowledgeQueryServiceIF(abc.ABC):
    @abc.abstractmethod
    async def query(self, provider_id: ConnectorId, query: KnowledgeQuery) -> list[Knowledge]:
        raise NotImplementedError

    # @abc.abstractmethod
    # async def query_llm(self):
    #     raise NotImplementedError
