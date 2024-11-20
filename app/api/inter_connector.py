from io import BytesIO

from api.dependencies.usecase import get_asset_catalog_usecase, get_knowledge_query_secure_usecase
from ddd.usecases.asset import AssetCatalogUsecase
from ddd.usecases.knowledge import KnowledgeQuerySecureUsecase
from ddd.usecases.schemas.knowledge import KnowledgeQueryDto
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from schemas.assets import AssetCatalogResponse
from schemas.knowledges import KnowledgeQueryRequest, KnowledgeResponse

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


@router.post("/knowledges", response_model=list[KnowledgeResponse])
async def retrieve_knowledge(
    query: KnowledgeQueryRequest,
    knowledge_query_usecase: KnowledgeQuerySecureUsecase = Depends(get_knowledge_query_secure_usecase),
):
    query_dto = KnowledgeQueryDto.model_validate(query, from_attributes=True)

    knowledge_dto_list = await knowledge_query_usecase.execute(query_dto)
    return [KnowledgeResponse.model_validate(knowledge, from_attributes=True) for knowledge in knowledge_dto_list]


# @router.post("/generate", response_model=protocol.GenerateResponse)
# async def generate_answer(req: protocol.GenerateRequest, llm_interface=Depends(get_llm_interface)):
#     answer: str = await llm_interface.generate(
#         model=req.model, user_prompt=req.user_prompt, system_prompt=req.system_prompt
#     )
#     return {"answer": answer}
