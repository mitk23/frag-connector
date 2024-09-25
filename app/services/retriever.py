import heapq
from typing import Literal

import httpx
from ddd.usecases import ConnectorUsecase
from fastapi import HTTPException, status


class FederatedRetriever:
    __RETRIEVE_API_PATH = "/api/protocol/retrieve"

    def __init__(
        self,
        retrievers: list[str] | None,
        connector_usecase: ConnectorUsecase,
        rerank: Literal["naive"] = "naive",
        include_contribution: bool = False,
    ):
        self.retrievers = retrievers
        if self.retrievers is None:
            self.retrievers = connector_usecase.list_connector_names()
        self.connector_usecase = connector_usecase
        self.rerank = rerank
        self.include_contribution = include_contribution

    async def retrieve(
        self, vector: list[float], top_k: int = 3, include_vector: bool = True, headers: dict = None
    ) -> list[dict]:
        json = {
            "query_vector": vector,
            "top_k": top_k,
            "include_vector": include_vector,
        }

        federated_retrieval_result = {}
        async with httpx.AsyncClient() as client:
            for retriever in self.retrievers:
                endpoint = self.__get_retrieval_endpoint(retriever)
                # retrieve_endpoint = retriever + __RETRIEVE_API_PATH
                try:
                    response = await client.post(endpoint, headers=headers, json=json)
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
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={
                            "message": "Retriever error",
                            "error": err.response.json(),
                        },
                    )
                retrieved_vector_list: list[dict] = response.json()
                federated_retrieval_result[retriever] = retrieved_vector_list

        if self.rerank == "naive":
            reranked_vector_list = self.rerank_naive(federated_retrieval_result, top_k)
        elif self.rerank == "cosine":
            ...
        else:
            all_vector_list = [v for vectors in federated_retrieval_result.values() for v in vectors]
            reranked_vector_list = sorted(all_vector_list, key=lambda vector: vector.get("score"), reverse=True)

        # TODO: 各コネクタの貢献度を算出する
        if self.include_contribution:
            ...

        return reranked_vector_list

    def rerank_naive(self, federated_retrieval_result: dict[str, list[dict]], top_k: int = 3) -> list[dict]:
        """
        検索したすべての関連文書から類似度スコア上位top_k個を取得する
        （類似度スコアがすべて同じmetricsに基づくことを前提とする）
        """
        heap = []
        for retriever, vectors in federated_retrieval_result.items():
            if len(vectors) == 0:
                continue
            score = vectors[0]["score"]
            heapq.heappush(heap, (-score, retriever, 0))

        reranked_vectors: list[dict] = []
        for _ in range(top_k):
            if len(heap) == 0:
                break

            _, retriever, _index = heapq.heappop(heap)

            vector: dict = federated_retrieval_result[retriever][_index]
            vector["retriever"] = retriever
            reranked_vectors.append(vector)

            if _index + 1 < len(federated_retrieval_result[retriever]):
                next_vector = federated_retrieval_result[retriever][_index + 1]
                heapq.heappush(heap, (-next_vector["score"], retriever, _index + 1))

        return reranked_vectors

    def __get_retrieval_endpoint(self, retriever_name: str) -> str:
        retriever_origin = self.connector_usecase.get_origin_from_name(retriever_name)
        if retriever_origin is None:
            retriever_origin = retriever_name

        retrieval_endpoint = retriever_origin + self.__RETRIEVE_API_PATH
        return retrieval_endpoint

    @classmethod
    def extract_context_from_result(cls, retrieval_result: list[dict]) -> list[str]:
        return [vector.get("text") for vector in retrieval_result]


# class FederatedRAGService:
#     __GENERATE_API_PATH = "/api/protocol/generate"

#     def __init__(
#         self,
#         llm_provider: str,
#         connector_usecase: ConnectorUsecase,
#         federated_retriever: FederatedRetriever | None = None,
#     ):
#         self.llm_provider = llm_provider
#         self.connector_usecase = connector_usecase
#         self.federated_retriever = federated_retriever

#     async def generate(
#         self,
#         query_text: str,
#         model: str,
#         headers: dict = None,
#     ):
#         ...

#     async def __generate(self, model: str, user_prompt: str, system_prompt: str, headers: dict = None):
#         endpoint = self.__get_generation_endpoint()

#         json = {"model": model, "user_prompt": user_prompt, "system_prompt": system_prompt}

#         async with httpx.AsyncClient() as client:
#             try:
#                 response = await client.post(endpoint, headers=headers, json=json)
#                 response.raise_for_status()
#             except httpx.RequestError as err:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail={
#                         "message": f"Error while requesting {err.request.url!r}",
#                     },
#                 )
#             except httpx.HTTPStatusError as err:
#                 raise HTTPException(
#                     status_code=status.HTTP_502_BAD_GATEWAY,
#                     detail={
#                         "message": f"Error in LLM connector: {err.request.url!r}",
#                         "error": err.response.json(),
#                     },
#                 )
#         return response.json()

#     def __get_generation_endpoint(self):
#         llm_provider_origin = self.connector_usecase.get_origin_from_name(self.llm_provider)
#         if llm_provider_origin is None:
#             llm_provider_origin = self.llm_provider

#         generation_endpoint = llm_provider_origin + self.__GENERATE_API_PATH
#         return generation_endpoint

#     @classmethod
#     def create_prompt(query_text: str, context: list[str] | None = None):
#         if context is None:
#             return query_text

#         return (
#             "Context information is below.\n"
#             "---------------------\n"
#             f"{'\n\n'.join(context)}\n"
#             "---------------------\n"
#             "Given the context information, answer the query.\n"
#             f"Query: {query_text}\n"
#             "Answer:"
#         )
