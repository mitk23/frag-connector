from api.dependencies.usecase import get_dataspace_frag_usecase, get_dataspace_usecase
from ddd.domains.qa import AnswerChunk, Question
from ddd.usecases.dataspace import DataspaceFRAGUsecase, DataspaceUsecase
from ddd.usecases.schemas.frag import FederatedRAGQueryDto
from ddd.usecases.schemas.knowledge import FederatedKnowledgeQueryDto
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from schemas.assets import AssetCatalogResponse
from schemas.frag import FederatedRAGRequest
from schemas.knowledges import FederatedKnowledgeQueryRequest, FederatedKnowledgeResponse
from schemas.qa import AnswerResponse, QuestionRequest

router = APIRouter()


@router.get("/catalogs", response_model=dict[str, AssetCatalogResponse])
async def list_asset_catalogs(
    provider_id: str,
    dataspace_usecase: DataspaceUsecase = Depends(get_dataspace_usecase),
):
    asset_catalogs = await dataspace_usecase.list_asset_catalogs(provider_id)
    return {
        _id: AssetCatalogResponse.model_validate(catalog, from_attributes=True)
        for _id, catalog in asset_catalogs.items()
    }


@router.get("/assets", response_class=StreamingResponse)
async def download_distribution(
    provider_id: str,
    asset_id: UUID4,
    distribution_title: str,
    dataspace_usecase: DataspaceUsecase = Depends(get_dataspace_usecase),
):
    distribution_content = await dataspace_usecase.download_distribution(provider_id, str(asset_id), distribution_title)
    return StreamingResponse(content=distribution_content.stream, media_type=distribution_content.media_type)


@router.post("/knowledges", response_model=list[FederatedKnowledgeResponse])
async def retrieve_knowledges(
    federated_knowledge_query: FederatedKnowledgeQueryRequest,
    dataspace_usecase: DataspaceUsecase = Depends(get_dataspace_usecase),
):
    federated_knowledge_query_dto = FederatedKnowledgeQueryDto.model_validate(
        federated_knowledge_query, from_attributes=True
    )
    federated_knowledge_list = await dataspace_usecase.retrieve_knowledges(federated_knowledge_query_dto)
    return [
        FederatedKnowledgeResponse.model_validate(knowledge, from_attributes=True)
        for knowledge in federated_knowledge_list
    ]


@router.post("/questions", response_class=StreamingResponse, response_model=AnswerChunk)
async def ask_question(
    provider_id: str, question: QuestionRequest, dataspace_usecase: DataspaceUsecase = Depends(get_dataspace_usecase)
):
    answer = await dataspace_usecase.ask_question(provider_id, Question.model_validate(question, from_attributes=True))
    answer_response = AnswerResponse.from_entity(answer)
    return StreamingResponse(content=answer_response.content, media_type="application/x-ndjson")


@router.post("/questions/frag", response_class=StreamingResponse, response_model=AnswerChunk)
async def federated_retrieve_and_generate(
    federated_rag_query: FederatedRAGRequest,
    dataspace_usecase: DataspaceFRAGUsecase = Depends(get_dataspace_frag_usecase),
):
    federated_rag_query_dto = FederatedRAGQueryDto.model_validate(federated_rag_query, from_attributes=True)
    print(federated_rag_query_dto)

    answer = await dataspace_usecase.execute(federated_rag_query_dto)
    answer_response = AnswerResponse.from_entity(answer)
    return StreamingResponse(content=answer_response.content, media_type="application/x-ndjson")
