import httpx
from api.dependencies.usecase import get_dataspace_usecase
from ddd.usecases.dataspace import DataspaceUsecase
from ddd.usecases.schemas.knowledge import FederatedKnowledgeQueryDto
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from schemas.assets import AssetCatalogResponse
from schemas.knowledges import FederatedKnowledgeQueryRequest, KnowledgeResponse

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


@router.post("/knowledges", response_model=list[KnowledgeResponse])
async def retrieve_knowledges(
    federated_knowledge_query: FederatedKnowledgeQueryRequest,
    dataspace_usecase: DataspaceUsecase = Depends(get_dataspace_usecase),
):
    federated_knowledge_query_dto = FederatedKnowledgeQueryDto.model_validate(
        federated_knowledge_query, from_attributes=True
    )
    knowledge_dto_list = await dataspace_usecase.retrieve_knowledges(federated_knowledge_query_dto)
    return [KnowledgeResponse.model_validate(knowledge, from_attributes=True) for knowledge in knowledge_dto_list]

    # # TODO: メタデータによるフィルタリング条件の指定パラメータを加える
    # federated_retriever = FederatedRetriever(
    #     retrievers=req.retrieval_providers,
    #     connector_usecase=connector_usecase,
    #     rerank=req.rerank,
    #     include_contribution=req.include_contribution,
    # )
    # retrieved_vector_list = await federated_retriever.retrieve(
    #     vector=req.query_vector, top_k=req.top_k, include_vector=req.include_vector, headers=headers
    # )
    # return retrieved_vector_list


# @router.post("/generate")
# async def generate(
#     req: management.GenerateRequest,
#     access_token: str = Depends(get_oauth_access_token),
#     connector_usecase: ConnectorUsecase = Depends(get_connector_usecase),
# ):
#     llm_connector_origin = connector_usecase.get_origin_from_name(req.llm_connector)
#     if llm_connector_origin is None:
#         # 登録済みのコネクタ名に一致しなければ、リクエストボディの値をoriginとみなす
#         llm_connector_origin = req.llm_connector

#     generation_endpoint = llm_connector_origin + __GENERATE_API_PATH

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#     }

#     answer = await __generate(
#         generation_endpoint=generation_endpoint,
#         model=req.model,
#         user_prompt=req.user_prompt,
#         system_prompt=req.system_prompt,
#         headers=headers,
#     )
#     return answer


# @router.post("/retrieve-and-generate")
# async def retrieve_and_generate(
#     req: management.FRAGRequest,
#     access_token: str = Depends(get_oauth_access_token),
#     connector_usecase: ConnectorUsecase = Depends(get_connector_usecase),
# ):
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#     }

#     # Retrieval Phase
#     federated_retriever = FederatedRetriever(
#         retrievers=req.retrieval_providers,
#         connector_usecase=connector_usecase,
#         rerank=req.rerank,
#         # include_contribution=req.include_contribution,
#     )
#     retrieved_vector_list = await federated_retriever.retrieve(
#         vector=req.query_vector, top_k=req.top_k, headers=headers
#     )

#     # Construct context and prompt
#     context = federated_retriever.extract_context_from_result(retrieved_vector_list)
#     user_prompt = create_rag_prompt(req.query_text, context)
#     print(user_prompt)

#     # Generation Phase
#     llm_connector_origin = connector_usecase.get_origin_from_name(req.llm_connector)
#     if llm_connector_origin is None:
#         # 登録済みのコネクタ名に一致しなければ、リクエストボディの値をoriginとみなす
#         llm_connector_origin = req.llm_connector

#     generation_endpoint = llm_connector_origin + __GENERATE_API_PATH

#     # TODO: FRAGの結果にretrieverや貢献度などの情報を加える
#     answer = await __generate(
#         generation_endpoint=generation_endpoint, model=req.model, user_prompt=user_prompt, headers=headers
#     )
#     return answer


async def __generate(
    generation_endpoint: str,
    model: str,
    user_prompt: str,
    system_prompt: str | None = None,
    headers: dict = None,
) -> dict[str, str]:
    json = {
        "model": model,
        "user_prompt": user_prompt,
        "system_prompt": system_prompt,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(generation_endpoint, headers=headers, json=json)
            response.raise_for_status()
        except httpx.RequestError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"Error while requesting {err.request.url!r}",
                },
            )
        except httpx.HTTPStatusError as err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": f"Error in LLM connector: {err.request.url!r}",
                    "error": err.response.json(),
                },
            )
    return response.json()


def create_rag_prompt(query: str, context: list[str]):
    return f"""
Context information is below.
---------------------
{'\n\n'.join(context)}
---------------------
Given the context information, answer the query.
Query: {query}
Answer:
"""
