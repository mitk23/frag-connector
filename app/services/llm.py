import abc
from typing import Literal

import httpx
from fastapi import HTTPException, status
from httpx import Response


class BaseLLMInterface(abc.ABC):
    def __init__(self, api_key: str | None, api_base_url: str) -> None:
        self.api_key = api_key
        self.api_base_url = api_base_url

    @abc.abstractmethod
    async def generate(self, model: str, user_prompt: str, system_prompt: str | None) -> str:
        # message: {"role": ..., "content": ...}
        raise NotImplementedError

    @classmethod
    def to_message(cls, content: str, role: Literal["user", "system"] = "user") -> dict:
        return {"role": role, "content": content}


class OpenAIInterface(BaseLLMInterface):
    def __init__(self, api_key: str | None, api_base_url: str) -> None:
        super().__init__(api_key, api_base_url)


class OllamaInterface(BaseLLMInterface):
    def __init__(self, api_key: str | None, api_base_url: str) -> None:
        super().__init__(api_key, api_base_url)

    async def generate(self, model: str, user_prompt: str, system_prompt: str | None = None) -> str:
        await self.__pull_model(model)

        user_message = self.to_message(user_prompt, role="user")
        if system_prompt is not None:
            messages = [self.to_message(system_prompt, role="system"), user_message]
        else:
            messages = [user_message]
        # TODO: streamに対応する
        json = {"model": model, "messages": messages, "stream": False}

        response = await self.__post("/api/chat", json=json)
        answer = response.json()["message"]["content"]
        return answer

    async def __post(self, api_path: str, headers: dict | None = None, json: dict | None = None) -> Response:
        endpoint = self.api_base_url + api_path

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, headers=headers, json=json)
                response.raise_for_status()
            except httpx.RequestError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": f"Error while requesting {err.request.url!r}"},
                )
            except httpx.HTTPStatusError as err:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"message": "Ollama error", "detail": err.response.json()},
                )
        return response

    async def __list_local_models(self) -> list[dict]:
        endp = self.api_base_url + "/api/tags"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(endp)
                response.raise_for_status()
            except httpx.RequestError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": f"Error while requesting {err.request.url!r}",
                    },
                )
            except httpx.HTTPStatusError:
                raise ValueError("Ollama error")

        result = response.json()
        return result["models"]

    async def __pull_model(self, model: str) -> None:
        json = {"name": model, "stream": False}

        response = await self.__post("/api/pull", json=json)
        pull_status: str | None = response.json().get("status", None)

        if pull_status is None or pull_status != "success":
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY)
        return
