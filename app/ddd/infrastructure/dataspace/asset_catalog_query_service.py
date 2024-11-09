import json
from typing import Any, AsyncGenerator

import httpx
from core.exceptions import InternalException
from ddd.domains.asset import AssetCatalog, AssetId, DistributionContent
from ddd.domains.connector import ConnectorId, ConnectorRepositoryIF
from ddd.domains.dataspace import DataspaceAssetCatalogQueryServiceIF
from ddd.usecases.schemas.asset import AssetCatalogDto
from ddd.usecases.schemas.connector import ConnectorDto


class DataspaceAssetCatalogQueryServiceImpl(DataspaceAssetCatalogQueryServiceIF):
    def __init__(
        self,
        dataspace_access_token: str,
        connector_repository: ConnectorRepositoryIF,
    ):
        self.__dataspace_access_token = dataspace_access_token
        self.__connector_repository = connector_repository

    def __handle_error(self, description: str, error: Exception | None = None):
        # TODO: dataspace用のexceptionを定義した方がよさそう
        raise InternalException(description=description, upstream_exc=error)

    async def __get_provider_url(self, provider_id: ConnectorId) -> str:
        provider = await self.__connector_repository.find_by_id(provider_id)
        if provider is None:
            self.__handle_error(description=f"Provider [{str(provider_id)}] not found")
        provider_dto = ConnectorDto.from_entity(provider)
        return provider_dto.url

    async def __get_find_endpoint(self, provider_id: ConnectorId) -> str:
        provider_url = await self.__get_provider_url(provider_id)
        return provider_url + "api/inter-connector/catalogs"

    async def __get_download_endpoint(self, provider_id: ConnectorId, asset_id: AssetId) -> str:
        provider_url = await self.__get_provider_url(provider_id)
        return provider_url + f"api/inter-connector/assets/{str(asset_id)}"

    async def __http_get(self, url: str, headers: dict[str, Any]) -> Any:
        # TODO: HTTPエラーオブジェクトの受け渡しの方法も考える（err.response.json()を表示できるようにしたい）
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(error=err, description=f"Error while requesting {err.request.url!r}")
            except httpx.HTTPStatusError as err:
                self.__handle_error(error=err, description=f"Error in counter connector: {err.request.url!r}")
        return response.json()

    async def __http_get_stream(
        self, url: str, headers: dict[str, Any], params: dict[str, Any]
    ) -> AsyncGenerator[bytes, None]:
        # TODO: HTTPエラーオブジェクトの受け渡しの方法も考える（err.response.json()を表示できるようにしたい）
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url=url, headers=headers, params=params) as response:
                # first: status code
                yield response.status_code
                # second: content type
                content_type: str = response.headers.get("content-type")
                yield content_type
                # third: content chunk
                async for chunk in response.aiter_bytes():
                    yield chunk

    async def find_all(self, provider_id: ConnectorId) -> dict[AssetId, AssetCatalog]:
        find_endpoint = await self.__get_find_endpoint(provider_id)

        try:
            asset_catalogs: dict[str, dict] = await self.__http_get(
                find_endpoint, headers={"Authorization": f"Bearer {self.__dataspace_access_token}"}
            )
        except InternalException as exc:
            self.__handle_error(description="Failed to fetch asset catalogs from dataspace", error=exc)

        asset_catalog_entity_list = {
            AssetId(value=_id): AssetCatalogDto.model_validate(asset).to_entity()
            for _id, asset in asset_catalogs.items()
        }
        # asset_dto_dict = {_id: AssetDto.model_validate(asset) for _id, asset in response_json.items()}
        # asset_entity_list = [asset_dto.to_entity() for asset_dto in asset_dto_dict.values()]
        return asset_catalog_entity_list

    async def find_by_id(self, provider_id: ConnectorId, asset_id: AssetId) -> AssetCatalog | None:
        find_endpoint = await self.__get_find_endpoint(provider_id) + f"/{str(asset_id)}"

        asset_catalog: dict[str, Any] = await self.__http_get(
            find_endpoint, headers={"Authorization": f"Bearer {self.__dataspace_access_token}"}
        )
        asset_catalog_entity = AssetCatalogDto.model_validate(asset_catalog).to_entity()
        return asset_catalog_entity

    async def download(
        self, provider_id: ConnectorId, asset_id: AssetId, distribution_title: str
    ) -> DistributionContent:
        pull_endpoint = await self.__get_download_endpoint(provider_id, asset_id)

        content_stream = self.__http_get_stream(
            pull_endpoint,
            headers={"Authorization": f"Bearer {self.__dataspace_access_token}"},
            params={"distribution_title": distribution_title},
        )

        # 1. extract response status code from stream
        status_code = await content_stream.__anext__()
        # 2. extract content type from stream
        content_type = await content_stream.__anext__()

        # remainings in stream are content chunks
        if status_code == 200:
            return DistributionContent(media_type=content_type, stream=content_stream)
        # error handling
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
                description="Failed to download asset from counter connector",
                error=InternalException(error_message),
            )
