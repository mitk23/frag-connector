import json
from typing import Any, AsyncGenerator

import httpx
from core.exceptions import InternalException
from ddd.domains.asset import Asset, AssetId, AssetRepositoryIF
from ddd.domains.connector import ConnectorId, ConnectorRepositoryIF
from ddd.domains.knowledge import Knowledge, KnowledgeQuery
from ddd.usecases.schemas.asset import AssetDto
from ddd.usecases.schemas.connector import ConnectorDto


class DataspaceQueryServiceImpl:
    def __init__(
        self,
        dataspace_access_token: str,
        asset_repository: AssetRepositoryIF,
        connector_repository: ConnectorRepositoryIF,
    ):
        self.__dataspace_access_token = dataspace_access_token

        self.__asset_repository = asset_repository
        self.__connector_repository = connector_repository

    def __handle_error(self, description: str, error: Exception | None = None):
        # TODO: dataspace用のexceptionを定義した方がよさそう
        raise InternalException(description=description, upstream_exc=error)

    async def __http_get_stream(self, url: str, headers: dict[str, Any]) -> AsyncGenerator[bytes, None]:
        # TODO: HTTPエラーオブジェクトの受け渡しの方法も考える（err.response.json()を表示できるようにしたい）
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url=url, headers=headers) as response:
                # first: status code
                yield response.status_code
                # second: content type
                content_type: str = response.headers.get("content-type")
                yield content_type
                # third: content chunk
                async for chunk in response.aiter_bytes():
                    yield chunk

    async def __http_get(self, url: str, headers: dict[str, Any]) -> httpx.Response:
        # TODO: HTTPエラーオブジェクトの受け渡しの方法も考える（err.response.json()を表示できるようにしたい）
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(error=err, description=f"Error while requesting {err.request.url!r}")
            except httpx.HTTPStatusError as err:
                self.__handle_error(error=err, description=f"Error in counter connector: {err.request.url!r}")
        return response

    async def __http_post(self, url: str, headers: dict[str, Any], json: dict[str, Any]) -> httpx.Response:
        # TODO: HTTPエラーオブジェクトの受け渡しの方法も考える（err.response.json()を表示できるようにしたい）
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=json)
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(error=err, description=f"Error while requesting {err.request.url!r}")
            except httpx.HTTPStatusError as err:
                self.__handle_error(error=err, description=f"Error in counter connector: {err.request.url!r}")
        return response

    async def __get_provider_url(self, provider_id: ConnectorId) -> str:
        provider = await self.__connector_repository.find_by_id(provider_id)
        if provider is None:
            self.__handle_error(description=f"Provider {str(provider_id)} not found")
        provider_dto = ConnectorDto.from_entity(provider)
        return provider_dto.url

    def __asset_list_endpoint(self, provider_url: str):
        return f"{provider_url}api/inter-connector/assets"

    def __asset_endpoint(self, provider_url: str, asset_id: str):
        return f"{provider_url}api/inter-connector/assets/{asset_id}"

    def __vector_query_endpoint(self, provider_url: str):
        raise NotImplementedError
        return provider_url + ...

    async def find_assets(self, provider_id: ConnectorId) -> list[Asset]:
        provider_url = await self.__get_provider_url(provider_id)

        asset_list_endpoint = self.__asset_list_endpoint(provider_url)
        response = await self.__http_get(
            asset_list_endpoint, headers={"Authorization": f"Bearer {self.__dataspace_access_token}"}
        )
        response_json: dict[str, dict] = response.json()

        asset_dto_dict = {_id: AssetDto.model_validate(asset) for _id, asset in response_json.items()}
        asset_entity_list = [asset_dto.to_entity() for asset_dto in asset_dto_dict.values()]
        return asset_entity_list

    async def pull_asset(self, provider_id: ConnectorId, asset_id: AssetId) -> tuple[str, AsyncGenerator[bytes, None]]:
        provider_url = await self.__get_provider_url(provider_id)

        asset_endpoint = self.__asset_endpoint(provider_url, str(asset_id))

        content_stream = self.__http_get_stream(
            asset_endpoint, headers={"Authorization": f"Bearer {self.__dataspace_access_token}"}
        )
        # first: extract response status code from stream
        status_code = await content_stream.__anext__()
        # second: extract content type from stream
        content_type = await content_stream.__anext__()

        if status_code == 200:
            # remainings are content chunks
            return content_type, content_stream
        else:
            # decode error message from byte stream
            error_bytes_list: list[bytes] = []
            async for chunk in content_stream:
                error_bytes_list.append(chunk)
            error_bytes = b"".join(error_bytes_list)

            if content_type == "application/json":
                # error object is formatted in connector exception
                error_obj: dict[str, Any] = json.loads(error_bytes)
                error_message = error_obj.get("description")
            else:
                error_message = error_bytes.decode()

            self.__handle_error(
                description="Failed to pull asset from counter connector",
                error=InternalException(error_message),
            )

    async def query_knowledge(self, provider_id: ConnectorId, query: KnowledgeQuery) -> list[Knowledge]:
        provider_url = self.__get_provider_url(provider_id)

        vector_query_endpoint = self.__vector_query_endpoint(provider_url)
        response = await self.__http_post(
            vector_query_endpoint,
            headers={"Authorization": f"Bearer {self.__dataspace_access_token}"},
            json=query.model_dump(),
        )

        vector_record_dto_list = [... for vector in response.json()]
        return [... for vector_dto in vector_record_dto_list]

    # @abc.abstractmethod
    # async def query_llm(self):
    #     raise NotImplementedError
