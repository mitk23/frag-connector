import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from core.exceptions import InternalException
from ddd.domains.connector import ConnectorId, ConnectorRepositoryIF
from ddd.domains.dataspace import DataspaceQAServiceIF
from ddd.domains.qa import Answer, AnswerChunk, Question


class DataspaceQAServiceImpl(DataspaceQAServiceIF):
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

    async def __get_question_endpoint(self, provider_id: ConnectorId) -> str:
        provider_url = await self.__get_provider_url(provider_id)
        return provider_url + "api/inter-connector/questions"

    async def __http_post_stream(
        self, _url: str, _headers: dict[str, Any], _json: dict[str, Any]
    ) -> AsyncGenerator[AnswerChunk]:
        time_start = time.perf_counter()
        async with httpx.AsyncClient(http2=True) as client:
            async with client.stream("POST", url=_url, headers=_headers, json=_json) as response:
                async for chunk in response.aiter_lines():
                    yield AnswerChunk.model_validate_json(chunk)
        print(f"[{self.__class__.__name__}.__http_post] {time.perf_counter() - time_start:.5f} [sec]")

    async def ask(self, provider_id: ConnectorId, question: Question) -> Answer:
        time_start = time.perf_counter()
        question_endpoint = await self.__get_question_endpoint(provider_id)

        answer_chunk_stream = self.__http_post_stream(
            question_endpoint,
            _headers={"Authorization": f"Bearer {self.__dataspace_access_token}"},
            _json=question.model_dump(),
        )
        print(f"[{self.__class__.__name__}.ask] {time.perf_counter() - time_start:.5f} [sec]")
        return Answer(content=answer_chunk_stream)
