from typing import Any

import httpx
from core.exceptions import InternalException
from ddd.domains.knowledge import Answer, Knowledge, QAServiceIF, Question

from .qa_model import MessageToLLM, QuestionOllamaDao


class OllamaQAService(QAServiceIF):
    def __init__(self, api_base_url: str, model: str, system_prompt: str | None = None) -> None:
        self.__api_base_url = api_base_url
        self.__model = model
        self.__system_prompt = system_prompt

    # TODO: handle_errorのerror引数にdefault値を設定する（ここ以外）
    def __handle_error(self, description: str, error: Exception | None = None):
        raise InternalException(description=description, upstream_exc=error)

    async def __http_post(
        self, url: str, headers: dict[str, Any] | None = None, json: dict[str, Any] | None = None
    ) -> httpx.Response:
        # TODO: HTTPエラーオブジェクトの受け渡しの方法も考える（err.response.json()を表示できるようにしたい）
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=json)
                response.raise_for_status()
            except httpx.RequestError as err:
                self.__handle_error(error=err, description=f"Error while requesting {err.request.url!r}")
            except httpx.HTTPStatusError as err:
                self.__handle_error(error=err, description=f"Error in Ollama: {err.request.url!r}")
        return response

    async def __pull_model(self) -> None:
        url = self.__api_base_url + "/api/pull"
        json = {"name": self.__model, "stream": False}

        response = await self.__http_post(url, json=json)
        status = response.json().get("status")

        if status is None or status != "success":
            self.__handle_error(description="Failed to pull a model from Ollama")

    async def ask(self, question: Question, knowledges: list[Knowledge] | None) -> Answer:
        await self.__pull_model()

        question_dao = QuestionOllamaDao(
            model=self.__model,
            messages=[
                MessageToLLM(content=self.__system_prompt, role="system"),
                MessageToLLM(content=question.text, role="user"),
            ],
            stream=True,
        )

        url = self.__api_base_url + "/api/chat"
        json = question_dao.model_dump()

        response = await self.__http_post(url, json=json)
        raise NotImplementedError
