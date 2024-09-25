from typing import Any

from core.exceptions import ConnectorException
from ddd.domains.asset import AssetId
from ddd.domains.connector import ConnectorId
from ddd.domains.dataspace import DataspaceAssetQueryServiceIF
from fastapi import status

from .schemas.asset import AssetCatalogDto
from .schemas.knowledge import KnowledgeQueryDto


class DataspaceUsecase:
    def __init__(self, asset_query_service: DataspaceAssetQueryServiceIF):
        self.__asset_query_service = asset_query_service

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_asset_catalogs(self, provider_id: str) -> dict[str, AssetCatalogDto]:
        catalogs = await self.__asset_query_service.find_all(ConnectorId(value=provider_id))
        return {str(_id): AssetCatalogDto.from_entity(catalog) for _id, catalog in catalogs.items()}

    async def pull_asset(self, provider_id: str, asset_id: str) -> dict[str, Any]:
        result = await self.__asset_query_service.pull(ConnectorId(value=provider_id), AssetId(value=asset_id))
        return result

    async def retrieve_documents(
        self, provider_id_list: list[str], knowledge_query: KnowledgeQueryDto, rerank_method: str
    ):
        raise NotImplementedError

    async def generate_text(self) -> str:
        raise NotImplementedError

    async def retrieve_and_generate(self) -> str:
        raise NotImplementedError
