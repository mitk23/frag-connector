from core.exceptions import ConnectorException
from ddd.domains.knowledge import KnowledgeQueryServiceIF
from fastapi import status

from .schemas.knowledge import KnowledgeDto, KnowledgeQueryDto


class KnowledgeUsecase:
    def __init__(self, knowledge_query_service: KnowledgeQueryServiceIF):
        self.__knowledge_query_service = knowledge_query_service

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def query(self, query: KnowledgeQueryDto) -> list[KnowledgeDto]:
        query_entity = query.to_entity()
        try:
            knowledge_entity_list = await self.__knowledge_query_service.query(query_entity)
        except Exception as exc:
            self.__handle_error(error=exc, description="Failed to query knowledge")

        # TODO: knowledgeの認可処理（-> dataspace APIの責務）
        return [KnowledgeDto.from_entity(kg_entity) for kg_entity in knowledge_entity_list]
