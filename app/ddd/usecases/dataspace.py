import asyncio

from core.exceptions import ConnectorException, InternalException
from ddd.domains.asset import AssetId
from ddd.domains.connector import ConnectorId
from ddd.domains.dataspace import DataspaceAssetCatalogQueryServiceIF, DataspaceKnowledgeQueryServiceIF
from ddd.domains.knowledge import FederatedKnowledge, FederatedKnowledgeList, KnowledgeQuery
from fastapi import status

from .schemas.asset import AssetCatalogDto, DistributionContentDto
from .schemas.knowledge import FederatedKnowledgeListDto, FederatedKnowledgeQueryDto


class DataspaceUsecase:
    def __init__(
        self,
        asset_catalog_query_service: DataspaceAssetCatalogQueryServiceIF,
        knowledge_query_service: DataspaceKnowledgeQueryServiceIF,
    ):
        self.__asset_catalog_query_service = asset_catalog_query_service
        self.__knowledge_query_service = knowledge_query_service

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_asset_catalogs(self, provider_id: str) -> dict[str, AssetCatalogDto]:
        try:
            catalogs = await self.__asset_catalog_query_service.find_all(ConnectorId(value=provider_id))
        except InternalException as exc:
            self.__handle_error(description=f"Failed to fetch asset catalogs from provier [{provider_id}]", error=exc)
        return {str(_id): AssetCatalogDto.from_entity(catalog) for _id, catalog in catalogs.items()}

    async def download_distribution(
        self, provider_id: str, asset_id: str, distribution_title: str
    ) -> DistributionContentDto:
        try:
            distribution_content = await self.__asset_catalog_query_service.download(
                ConnectorId(value=provider_id), AssetId(value=asset_id), distribution_title
            )
        except InternalException as exc:
            self.__handle_error(
                description=f"Failed to download distribution [{distribution_title}] from provider [{provider_id}]",
                error=exc,
            )
        return DistributionContentDto.from_entity(distribution_content)

    async def retrieve_knowledges(
        self, federated_knowledge_query: FederatedKnowledgeQueryDto
    ) -> FederatedKnowledgeListDto:
        async def __retrieve(provider_id: ConnectorId, query: KnowledgeQuery):
            knowledges = await self.__knowledge_query_service.execute(provider_id, query)
            federated_knowledge_list.append_list(
                [FederatedKnowledge.from_knowledge(knowledge, provider_id) for knowledge in knowledges]
            )

        query = federated_knowledge_query.query
        providers = federated_knowledge_query.providers

        federated_knowledge_list: FederatedKnowledgeList = FederatedKnowledgeList()
        try:
            async with asyncio.TaskGroup() as tg:
                for provider in providers:
                    provider_id = ConnectorId(value=provider)
                    tg.create_task(__retrieve(provider_id, query.to_entity()))
        except* Exception as err:
            print(f"{err.exceptions=}")

        # for provider in providers:
        #     provider_id = ConnectorId(value=provider)
        #     knowledges = await self.__knowledge_query_service.execute(provider_id, query.to_entity())
        #     federated_knowledge_list.append_list(
        #         [FederatedKnowledge.from_knowledge(knowledge, provider_id) for knowledge in knowledges]
        #     )

        if federated_knowledge_query.knowledge_rerank_method is not None:
            federated_knowledge_list = federated_knowledge_list.rerank(
                method=federated_knowledge_query.knowledge_rerank_method,
                top_k=federated_knowledge_query.return_num_knowledges,
                query_embedding=query.embedding,
            )
        return FederatedKnowledgeListDto.from_entity(federated_knowledge_list)

    async def generate_text(self) -> str:
        raise NotImplementedError

    async def retrieve_and_generate(self) -> str:
        raise NotImplementedError
