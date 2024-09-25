import httpx
from core.exceptions import ConnectorException
from ddd.domains.asset import Asset, AssetId, AssetRepositoryIF, AssetSecurityLevel
from fastapi import status

from .schemas.asset import AssetCreateDto, AssetDto, AssetUpdateDto


class AssetUsecase:
    def __init__(self, asset_repository: AssetRepositoryIF):
        self.__asset_repository = asset_repository

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def list_assets(self) -> dict[str, AssetDto]:
        assets = await self.__asset_repository.find_all()
        return {str(_id): AssetDto.from_entity(asset) for _id, asset in assets.items()}

    async def get_asset(self, asset_id: str) -> AssetDto:
        asset = await self.__asset_repository.find_by_id(AssetId(value=asset_id))
        if asset is None:
            self.__handle_error(status_code=status.HTTP_404_NOT_FOUND, description=f"Asset ID={asset_id}` not found")
        return AssetDto.from_entity(asset)

    async def create_asset(self, new_asset: AssetCreateDto) -> AssetDto:
        assets = await self.__asset_repository.find_all()

        for asset in assets.values():
            if asset.name == new_asset.name:
                self.__handle_error(
                    status_code=status.HTTP_409_CONFLICT, description=f"Asset `{new_asset.name}` is already existed"
                )

        new_asset_entity = Asset(
            id=None,
            name=new_asset.name,
            url=new_asset.url,
            title=new_asset.title,
            description=new_asset.description,
            content_type=new_asset.content_type,
            security=AssetSecurityLevel.generate(new_asset.security),
        )
        try:
            created_asset = await self.__asset_repository.save(new_asset_entity)
        except Exception as exc:
            self.__handle_error(description="Failed to create a new asset", error=exc)

        return AssetDto.from_entity(created_asset)

    async def update_asset(self, asset_id: str, new_asset: AssetUpdateDto) -> None:
        old_asset = await self.__asset_repository.find_by_id(AssetId(value=asset_id))

        if old_asset is None:
            self.__handle_error(status_code=status.HTTP_404_NOT_FOUND, description=f"Asset ID={asset_id}` not found")
        if asset_id != new_asset.id:
            self.__handle_error(status_code=status.HTTP_400_BAD_REQUEST, description="Invalid asset update request")

        new_asset_dto = AssetDto.model_validate(new_asset.model_dump())
        new_asset_entity = new_asset_dto.to_entity()

        try:
            await self.__asset_repository.save(new_asset_entity)
        except Exception as exc:
            self.__handle_error(description=f"Failed to update the asset: {asset_id}", error=exc)

    async def delete_asset(self, asset_id: str) -> None:
        try:
            await self.__asset_repository.delete(AssetId(value=asset_id))
        except Exception as exc:
            self.__handle_error(description=f"Failed to delete the asset: {asset_id}", error=exc)

    async def pull_asset(self, asset_id: str) -> bytes:
        asset_dto = await self.get_asset(asset_id)
        asset_url = asset_dto.url

        if asset_url is None:
            self.__handle_error(
                status_code=status.HTTP_404_NOT_FOUND, description=f"Asset ({asset_id}) URL is not registered"
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(asset_url)
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(description=f"Error while requesting {err.request.url!r}", error=err)
            except httpx.HTTPStatusError as err:
                self.__handle_error(description=f"Error on fetching the asset: {err.request.url!r}", error=err)

        asset_content = response.content
        return asset_content
