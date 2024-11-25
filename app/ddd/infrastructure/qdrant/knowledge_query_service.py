from core.exceptions import InternalException
from ddd.domains.knowledge import Knowledge, KnowledgeQuery, KnowledgeQueryServiceIF
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from .knowledge_model import (
    KnowledgeQdrantDao,
    KnowledgeQueryQdrantDao,
)


class QdrantKnowledgeQueryService(KnowledgeQueryServiceIF):
    def __init__(self, url: str, api_key: str, index_name: str, text_key_in_metadata: str = "text") -> None:
        self.__url = url
        self.__api_key = api_key
        self.__index_name = index_name
        self.__text_key_in_metadata = text_key_in_metadata

        self.__client: AsyncQdrantClient = AsyncQdrantClient(url=self.__url, api_key=self.__api_key)

    def __handle_error(self, description: str, error: Exception | None = None):
        raise InternalException(description=description, upstream_exc=error)

    async def execute(self, query: KnowledgeQuery) -> list[Knowledge]:
        query_dao = KnowledgeQueryQdrantDao.from_entity(query)
        try:
            response = await self.__client.search(
                collection_name=self.__index_name,
                query_vector=query_dao.query_vector,
                query_filter=query_dao.query_filter,
                limit=query_dao.limit,
                with_vectors=query_dao.with_vectors,
                with_payload=query_dao.with_payload,
            )
        except UnexpectedResponse as exc:
            self.__handle_error(description="Failed to query vectors from Qdrant", error=exc)

        knowledge_dao_list = [KnowledgeQdrantDao.model_validate(point, from_attributes=True) for point in response]
        return [
            knowledge_dao.to_entity(text_key_in_metadata=self.__text_key_in_metadata)
            for knowledge_dao in knowledge_dao_list
        ]

    async def fetch(self, knowledge_id_list: list[str]) -> list[Knowledge]:
        raise NotImplementedError
