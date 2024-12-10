from collections.abc import AsyncGenerator, AsyncIterator

import ollama
from core.exceptions import InternalException
from ddd.domains.qa import Answer, AnswerChunk, QAServiceIF, Question

from .qa_model import OllamaQuestionMessage


class OllamaQAService(QAServiceIF):
    def __init__(self, api_base_url: str) -> None:
        self.__api_base_url = api_base_url

        self.__client = ollama.AsyncClient(host=self.__api_base_url)

    def __handle_error(self, description: str, error: Exception | None = None):
        raise InternalException(description=description, upstream_exc=error)

    async def __pull_model(self, model: str) -> None:
        response = await self.__client.pull(model)

        if response.status is None or response.status != "success":
            self.__handle_error(description="Failed to pull a model from Ollama")

    async def __get_answer_stream(self, response: AsyncIterator[ollama.ChatResponse]) -> AsyncGenerator[AnswerChunk]:
        async for chunk in response:
            yield AnswerChunk(model=chunk.model, text=chunk.message.content)

    async def ask(self, question: Question) -> Answer:
        await self.__pull_model(question.model)

        messages = [OllamaQuestionMessage.from_question(question).to_ollama_message()]

        response = await self.__client.chat(model=question.model, messages=messages, stream=True)
        answer_stream = self.__get_answer_stream(response)
        return Answer(content=answer_stream)
