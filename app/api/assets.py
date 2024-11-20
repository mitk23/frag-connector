from api.dependencies.usecase import get_asset_command_usecase, get_asset_query_usecase
from ddd.usecases.asset import AssetCommandUsecase, AssetQueryUsecase
from ddd.usecases.schemas.asset import AssetCreateDto, AssetUpdateDto
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import UUID4
from schemas.assets import AssetCreateRequest, AssetResponse, AssetUpdateRequest

router = APIRouter()


@router.get("", response_model=dict[str, AssetResponse])
async def list_assets(asset_usecase: AssetQueryUsecase = Depends(get_asset_query_usecase)):
    asset_dto_dict = await asset_usecase.list_assets()
    return {_id: AssetResponse.from_dict(asset_dto.model_dump()) for _id, asset_dto in asset_dto_dict.items()}


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: UUID4, asset_usecase: AssetQueryUsecase = Depends(get_asset_query_usecase)):
    asset_dto = await asset_usecase.get_asset(str(asset_id))
    return AssetResponse.from_dict(asset_dto.model_dump())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreateRequest,
    request: Request,
    response: Response,
    asset_usecase: AssetCommandUsecase = Depends(get_asset_command_usecase),
):
    asset_dto = AssetCreateDto.model_validate(asset.to_dict())
    created_asset = await asset_usecase.create_asset(asset_dto)
    response.headers["Location"] = f"{str(request.url)}/{created_asset.id}"


@router.put("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_asset(
    asset_id: UUID4,
    new_asset: AssetUpdateRequest,
    asset_usecase: AssetCommandUsecase = Depends(get_asset_command_usecase),
):
    new_asset_dto = AssetUpdateDto.model_validate(new_asset.to_dict())
    await asset_usecase.update_asset(str(asset_id), new_asset_dto)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID4,
    asset_usecase: AssetCommandUsecase = Depends(get_asset_command_usecase),
):
    await asset_usecase.delete_asset(str(asset_id))
