from io import BytesIO

from api.dependencies.usecase import get_asset_catalog_usecase
from ddd.usecases.asset import AssetCatalogUsecase
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from schemas.assets import AssetCatalogResponse

router = APIRouter()


@router.get("/catalogs", response_model=dict[str, AssetCatalogResponse])
async def list_asset_catalogs(
    asset_catalog_usecase: AssetCatalogUsecase = Depends(get_asset_catalog_usecase),
):
    asset_catalogs = await asset_catalog_usecase.list_asset_catalogs()
    return {
        _id: AssetCatalogResponse.model_validate(asset_catalog, from_attributes=True)
        for _id, asset_catalog in asset_catalogs.items()
    }


@router.get("/catalogs/{asset_id}", response_model=AssetCatalogResponse)
async def get_asset_catalog(
    asset_id: UUID4,
    asset_catalog_usecase: AssetCatalogUsecase = Depends(get_asset_catalog_usecase),
):
    asset_catalog = await asset_catalog_usecase.get_asset_catalog(str(asset_id))
    return AssetCatalogResponse.model_validate(asset_catalog, from_attributes=True)


@router.get("/assets/{asset_id}", response_class=StreamingResponse)
async def download_distribution(
    asset_id: UUID4,
    distribution_title: str,
    asset_catalog_usecase: AssetCatalogUsecase = Depends(get_asset_catalog_usecase),
):
    distribution = await asset_catalog_usecase.download_distribution(str(asset_id), distribution_title)
    return StreamingResponse(content=BytesIO(distribution.content), media_type=distribution.media_type)


# @router.post("/retrieve", response_model=protocol.RetrieveResponse)
# async def retrieve(
#     req: protocol.RetrieveRequest,
#     access_token: str = Depends(get_bearer_token),
#     vector_db=Depends(get_knowledge_query_service),
#     authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
# ):
#     # TODO: top_kのうちから返せるものだけを返すのか、認可をした上でtop_kを返すのか
#     retrieved_vectors: list[dict] = vector_db.query(
#         vector=req.query_vector,
#         top_k=req.top_k,
#         include_vector=req.include_vector,
#     )

#     # TODO: IDだけではなくメタデータ（文書ID, 文書集合ID）による認可判断にも対応する
#     retrieved_vector_ids = [v.get("id") for v in retrieved_vectors]
#     authorized_vector_id_set = await authorization_usecase.get_authorized_resource_set(
#         access_token, retrieved_vector_ids
#     )
#     authorized_vectors = [v for v in retrieved_vectors if v.get("id") in authorized_vector_id_set]
#     return authorized_vectors


# @router.post("/generate", response_model=protocol.GenerateResponse)
# async def generate_answer(req: protocol.GenerateRequest, llm_interface=Depends(get_llm_interface)):
#     answer: str = await llm_interface.generate(
#         model=req.model, user_prompt=req.user_prompt, system_prompt=req.system_prompt
#     )
#     return {"answer": answer}
