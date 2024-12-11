import time
from typing import Any

import httpx
from core.exceptions import InternalException
from ddd.domains.connector import ConnectorId, ConnectorRepositoryIF
from ddd.domains.dataspace import DataspaceKnowledgeQueryServiceIF
from ddd.domains.knowledge import Knowledge, KnowledgeQuery
from ddd.usecases.schemas.knowledge import KnowledgeDto


class DataspaceKnowledgeQueryServiceImpl(DataspaceKnowledgeQueryServiceIF):
    def __init__(self, dataspace_access_token: str, connector_repository: ConnectorRepositoryIF):
        self.__dataspace_access_token = dataspace_access_token
        self.__connector_repository = connector_repository

    def __handle_error(self, description: str, error: Exception | None = None):
        raise InternalException(description=description, upstream_exc=error)

    async def __get_provider_url(self, provider_id: ConnectorId) -> str:
        provider = await self.__connector_repository.find_by_id(provider_id)
        if provider is None:
            self.__handle_error(description=f"Provider [{str(provider_id)}] not found")
        return str(provider.url)

    async def __get_retrieve_endpoint(self, provider_id: ConnectorId) -> str:
        provider_url = await self.__get_provider_url(provider_id)
        return provider_url + "api/inter-connector/knowledges"

    async def __http_post(self, url: str, headers: dict[str, Any], json: dict[str, Any]) -> httpx.Response:
        time_start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=json)
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(error=err, description=f"Error while requesting {err.request.url!r}")
            except httpx.HTTPStatusError as err:
                self.__handle_error(error=err, description=f"Error in counter connector: {err.request.url!r}")
        print(f"[{self.__class__.__name__}.__http_post] {time.perf_counter() - time_start:.5f} [sec]")
        return response

    async def execute(self, provider_id: ConnectorId, query: KnowledgeQuery) -> list[Knowledge]:
        time_start_execute = time.perf_counter()

        retrieve_endpoint = await self.__get_retrieve_endpoint(provider_id)

        response = await self.__http_post(
            retrieve_endpoint,
            headers={"Authorization": f"Bearer {self.__dataspace_access_token}"},
            json=query.model_dump(),
        )
        knowledge_dict_list: list[dict[str, Any]] = response.json()

        knowledge_entity_list = [
            KnowledgeDto.model_validate(knowledge).to_entity() for knowledge in knowledge_dict_list
        ]
        print(f"[{self.__class__.__name__}.execute] {time.perf_counter() - time_start_execute:.5f} [sec]")
        return knowledge_entity_list

    async def fetch(self, knowledge_id_list: list[str]) -> list[Knowledge]:
        raise NotImplementedError
