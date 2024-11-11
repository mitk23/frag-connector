from core.exceptions import InternalException
from ddd.domains.knowledge import Knowledge, KnowledgeQuery, KnowledgeQueryServiceIF
from pinecone.exceptions import PineconeException
from pinecone.grpc import PineconeGRPC as Pinecone

from .knowledge_model import (
    KnowledgeFetchResponsePineconeDao,
    KnowledgeQueryPineconeDao,
    KnowledgeQueryResponsePineconeDao,
)


class PineconeKnowledgeQueryService(KnowledgeQueryServiceIF):
    def __init__(self, api_key: str, index_name: str, text_key_in_metadata: str = "text") -> None:
        self.__api_key = api_key
        self.__index_name = index_name
        self.__text_key_in_metadata = text_key_in_metadata

        self.__client: Pinecone = Pinecone(api_key=self.__api_key)
        self.index = self.__client.Index(self.__index_name)

    def __handle_error(self, description: str, error: Exception | None = None):
        raise InternalException(description=description, upstream_exc=error)

    async def execute(self, query: KnowledgeQuery) -> list[Knowledge]:
        query_dao = KnowledgeQueryPineconeDao.from_entity(query)
        try:
            query_response = self.index.query(
                vector=query_dao.vector,
                top_k=query_dao.top_k,
                include_values=query_dao.include_values,
                include_metadata=query_dao.include_metadata,
                filter=query_dao.filter,
            )
        except PineconeException as exc:
            self.__handle_error(exc, description="Failed to query vectors from Pinecone")

        query_response_dao = KnowledgeQueryResponsePineconeDao.model_validate(query_response.to_dict())
        knowledge_dao_list = query_response_dao.matches

        return [
            knowledge_dao.to_entity(text_key_in_metadata=self.__text_key_in_metadata)
            for knowledge_dao in knowledge_dao_list
        ]

    async def fetch(self, knowledge_id_list: list[str]) -> list[Knowledge]:
        try:
            fetch_response = self.index.fetch(ids=knowledge_id_list)
        except PineconeException as exc:
            self.__handle_error(exc, description="Failed to fetch vectors from Pinecone")

        fetch_response_dao = KnowledgeFetchResponsePineconeDao.model_validate(fetch_response.to_dict())
        knowledge_dao_list = fetch_response_dao.vectors.values()

        return [
            knowledge_dao.to_entity(text_key_in_metadata=self.__text_key_in_metadata)
            for knowledge_dao in knowledge_dao_list
        ]


class QdrantKnowledgeQueryService(KnowledgeQueryServiceIF):
    def query(self, query: KnowledgeQuery) -> list[Knowledge]:
        raise NotImplementedError

    def fetch(self, knowledge_id_list: list[str]) -> list[Knowledge]:
        raise NotImplementedError
