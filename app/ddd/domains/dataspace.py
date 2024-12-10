import abc

from ddd.domains.asset import AssetCatalog, AssetId, DistributionContent
from ddd.domains.connector import ConnectorId
from ddd.domains.knowledge import Knowledge, KnowledgeQuery
from ddd.domains.qa import Answer, Question


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
    async def execute(self, provider_id: ConnectorId, query: KnowledgeQuery) -> list[Knowledge]:
        raise NotImplementedError


class DataspaceQAServiceIF(abc.ABC):
    @abc.abstractmethod
    async def ask(self, provider_id: ConnectorId, question: Question) -> Answer:
        raise NotImplementedError
