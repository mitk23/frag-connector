from api.dependencies.usecase import get_asset_usecase, get_authorization_usecase
from ddd.usecases.asset import AssetUsecase
from ddd.usecases.authorization import AuthorizationUsecase
from ddd.usecases.schemas.asset import AssetCreateDto, AssetUpdateDto
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import UUID4
from schemas.management import (
    AssetCreateRequest,
    AssetResponse,
    AssetUpdateRequest,
)

router = APIRouter()


@router.get("", response_model=dict[str, AssetResponse])
async def list_assets(asset_usecase: AssetUsecase = Depends(get_asset_usecase)):
    asset_dto_dict = await asset_usecase.list_assets()
    return {_id: AssetResponse.from_dict(asset_dto.model_dump()) for _id, asset_dto in asset_dto_dict.items()}


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: UUID4, asset_usecase: AssetUsecase = Depends(get_asset_usecase)):
    asset_dto = await asset_usecase.get_asset(str(asset_id))
    return AssetResponse.from_dict(asset_dto.model_dump())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreateRequest,
    request: Request,
    response: Response,
    asset_usecase: AssetUsecase = Depends(get_asset_usecase),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
):
    # TODO: transaction
    asset_dto = AssetCreateDto.model_validate(asset.to_dict())
    created_asset = await asset_usecase.create_asset(asset_dto)
    response.headers["Location"] = f"{str(request.url)}/{created_asset.id}"

    await authorization_usecase.create_asset_permission(
        asset_id=created_asset.id, asset_security_level=created_asset.security
    )


@router.put("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_asset(
    asset_id: UUID4,
    new_asset: AssetUpdateRequest,
    asset_usecase: AssetUsecase = Depends(get_asset_usecase),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
):
    # TODO: transaction
    asset_id_str = str(asset_id)

    old_asset_dto = await asset_usecase.get_asset(asset_id_str)

    new_asset_dto = AssetUpdateDto.model_validate(new_asset.to_dict())
    await asset_usecase.update_asset(asset_id_str, new_asset_dto)

    if new_asset_dto.security != old_asset_dto.security:
        await authorization_usecase.update_asset_permission(asset_id_str, new_asset_dto.security)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID4,
    asset_usecase: AssetUsecase = Depends(get_asset_usecase),
):
    # by deleting asset from keycloak, it automatically excluded from the permission resources
    await asset_usecase.delete_asset(str(asset_id))
    # await authorization_usecase.delete_asset_permission(str(asset_id))
