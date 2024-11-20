from core.exceptions import ConnectorException
from ddd.domains import domain_service
from ddd.domains.asset import AssetId, AssetRepositoryIF
from ddd.domains.authorization import AuthRepositoryIF
from ddd.domains.knowledge import KnowledgeQueryServiceIF
from fastapi import status

from .schemas.knowledge import KnowledgeDto, KnowledgeQueryDto


class KnowledgeQueryUsecase:
    def __init__(self, knowledge_query_service: KnowledgeQueryServiceIF):
        self.__knowledge_query_service = knowledge_query_service

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def execute(self, query: KnowledgeQueryDto) -> list[KnowledgeDto]:
        query_entity = query.to_entity()
        try:
            knowledge_entity_list = await self.__knowledge_query_service.execute(query_entity)
        except Exception as exc:
            self.__handle_error(error=exc, description="Failed to query knowledge")

        return [KnowledgeDto.from_entity(kg_entity) for kg_entity in knowledge_entity_list]


class KnowledgeQuerySecureUsecase(KnowledgeQueryUsecase):
    def __init__(
        self,
        knowledge_query_service: KnowledgeQueryServiceIF,
        asset_repository: AssetRepositoryIF,
        auth_repository: AuthRepositoryIF,
        knowledge_access_token: str,
    ):
        super().__init__(knowledge_query_service)

        self.__asset_repository = asset_repository
        self.__auth_repository = auth_repository
        self.__knowledge_access_token = knowledge_access_token

    async def __authorize_knowledges(self, knowledges: list[KnowledgeDto]) -> list[KnowledgeDto]:
        assets = await self.__asset_repository.find_all()

        # list asset id related to queried knowledge
        related_asset_id_set: set[AssetId] = set()
        for asset_id, asset in assets.items():
            if asset.vectors is not None:
                if asset.usage_policy.security_level.to_number() <= 30:
                    related_asset_id_set.add(asset_id)

        # authorization
        authorized_asset_id_set = await self.__auth_repository.authorized_resources(
            self.__knowledge_access_token, list(related_asset_id_set)
        )

        # only returns knowledges whose parent asset is authorized
        authorized_knowledge_list: list[KnowledgeDto] = []
        for knowledge in knowledges:
            authorized = False
            for asset_id in authorized_asset_id_set:
                vector_filter = assets.get(asset_id).vectors

                authorized |= domain_service.filter_knowledge_vector(knowledge, vector_filter)

            if authorized:
                authorized_knowledge_list.append(knowledge)

        return authorized_knowledge_list

    async def execute(self, query: KnowledgeQueryDto) -> list[KnowledgeDto]:
        knowledge_dto_list = await super().execute(query)

        authorized_knowledge_dto_list = await self.__authorize_knowledges(knowledge_dto_list)
        return authorized_knowledge_dto_list
