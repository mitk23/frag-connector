from io import BytesIO

from api.dependencies.auth import get_bearer_token
from api.dependencies.infrastructure import get_knowledge_query_service
from api.dependencies.usecase import get_asset_usecase, get_authorization_usecase
from core.exceptions import ConnectorException
from ddd.usecases.asset import AssetUsecase
from ddd.usecases.authorization import AuthorizationUsecase
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from schemas import protocol
from schemas.management import AssetResponse

router = APIRouter()


@router.get("/catalogs", response_model=dict[str, AssetResponse])
async def list_asset_catalogs(
    asset_usecase: AssetUsecase = Depends(get_asset_usecase),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
    access_token: str = Depends(get_bearer_token),
):
    # TODO: urlなどのフィールドは秘匿するべき
    # __exclude_fields = ["url", "security"]

    asset_dto_dict = await asset_usecase.list_assets()

    asset_id_list = list(asset_dto_dict.keys())
    authorized_asset_id_set = await authorization_usecase.authorized_resources(access_token, asset_id_list)

    authorized_asset_dict = {
        _id: AssetResponse.from_dict(asset_dto.model_dump())
        for _id, asset_dto in asset_dto_dict.items()
        if _id in authorized_asset_id_set
    }
    return authorized_asset_dict


@router.get("/catalogs/{asset_id}", response_model=AssetResponse)
async def get_asset_catalog(
    asset_usecase: AssetUsecase = Depends(get_asset_usecase),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
    access_token: str = Depends(get_bearer_token),
):
    raise NotImplementedError


@router.get("/assets/{asset_id}", response_class=StreamingResponse)
async def pull_asset(
    asset_id: UUID4,
    asset_usecase: AssetUsecase = Depends(get_asset_usecase),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
    access_token: str = Depends(get_bearer_token),
):
    asset_dto = await asset_usecase.get_asset(str(asset_id))
    is_authorized = await authorization_usecase.authorize(access_token, asset_dto)

    if not is_authorized:
        raise ConnectorException(
            status_code=status.HTTP_403_FORBIDDEN, description="Resouce access denied. You don't have permission."
        )

    asset_content = await asset_usecase.pull_asset(asset_dto.id)

    asset_content_type = asset_dto.content_type
    if asset_content_type is None:
        asset_content_type = "application/octet-stream"

    return StreamingResponse(content=BytesIO(asset_content), media_type=asset_content_type)


@router.post("/retrieve", response_model=protocol.RetrieveResponse)
async def retrieve(
    req: protocol.RetrieveRequest,
    access_token: str = Depends(get_bearer_token),
    vector_db=Depends(get_knowledge_query_service),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
):
    # TODO: top_kのうちから返せるものだけを返すのか、認可をした上でtop_kを返すのか
    retrieved_vectors: list[dict] = vector_db.query(
        vector=req.query_vector,
        top_k=req.top_k,
        include_vector=req.include_vector,
    )

    # TODO: IDだけではなくメタデータ（文書ID, 文書集合ID）による認可判断にも対応する
    retrieved_vector_ids = [v.get("id") for v in retrieved_vectors]
    authorized_vector_id_set = await authorization_usecase.get_authorized_resource_set(
        access_token, retrieved_vector_ids
    )
    authorized_vectors = [v for v in retrieved_vectors if v.get("id") in authorized_vector_id_set]
    return authorized_vectors


# @router.post("/generate", response_model=protocol.GenerateResponse)
# async def generate_answer(req: protocol.GenerateRequest, llm_interface=Depends(get_llm_interface)):
#     answer: str = await llm_interface.generate(
#         model=req.model, user_prompt=req.user_prompt, system_prompt=req.system_prompt
#     )
#     return {"answer": answer}
