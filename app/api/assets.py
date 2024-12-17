from api.dependencies.usecase import get_asset_command_usecase, get_asset_query_usecase
from ddd.usecases.asset import AssetCommandUsecase, AssetQueryUsecase
from ddd.usecases.schemas.asset import AssetCreateDto, AssetUpdateDto
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import UUID4
from schemas.assets import AssetCreateRequest, AssetResponse, AssetUpdateRequest

router = APIRouter()


@router.get(
    "",
    response_model=dict[str, AssetResponse],
    summary="コネクタ管理アセットの一覧",
    response_description="コネクタ管理アセットの一覧",
)
async def list_assets(asset_usecase: AssetQueryUsecase = Depends(get_asset_query_usecase)):
    """
    コネクタが管理・提供するアセットの情報を一覧取得するエンドポイント
    """
    asset_dto_dict = await asset_usecase.list_assets()
    return {_id: AssetResponse.from_dict(asset_dto.model_dump()) for _id, asset_dto in asset_dto_dict.items()}


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="コネクタ管理アセットの表示",
    response_description="コネクタ管理アセットの情報",
)
async def get_asset(asset_id: UUID4, asset_usecase: AssetQueryUsecase = Depends(get_asset_query_usecase)):
    """
    コネクタが管理・提供するアセットからアセットIDを指定して情報を取得するエンドポイント
    """
    asset_dto = await asset_usecase.get_asset(str(asset_id))
    return AssetResponse.from_dict(asset_dto.model_dump())


@router.post("", status_code=status.HTTP_201_CREATED, summary="コネクタ管理アセットの新規登録")
async def create_asset(
    asset: AssetCreateRequest,
    request: Request,
    response: Response,
    asset_usecase: AssetCommandUsecase = Depends(get_asset_command_usecase),
):
    """
    コネクタが管理・提供するアセットの情報を新たに登録するエンドポイント\n
    コネクタを介してデータスペースにデータ提供を行う場合、このエンドポイントを用いて事前にアセットを登録する必要がある
    """
    asset_dto = AssetCreateDto.model_validate(asset.to_dict())
    created_asset = await asset_usecase.create_asset(asset_dto)
    response.headers["Location"] = f"{str(request.url)}/{created_asset.id}"


@router.put("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="コネクタ管理アセットの更新")
async def update_asset(
    asset_id: UUID4,
    new_asset: AssetUpdateRequest,
    asset_usecase: AssetCommandUsecase = Depends(get_asset_command_usecase),
):
    """
    コネクタが管理・提供するアセットの情報を更新するエンドポイント
    """
    new_asset_dto = AssetUpdateDto.model_validate(new_asset.to_dict())
    await asset_usecase.update_asset(str(asset_id), new_asset_dto)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="コネクタ管理アセットの削除")
async def delete_asset(
    asset_id: UUID4,
    asset_usecase: AssetCommandUsecase = Depends(get_asset_command_usecase),
):
    """
    コネクタが管理・提供するアセットの情報を削除するエンドポイント
    """
    await asset_usecase.delete_asset(str(asset_id))
