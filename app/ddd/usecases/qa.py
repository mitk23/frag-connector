from core.exceptions import ConnectorException
from ddd.domains.qa import Answer, QAServiceIF, Question
from fastapi import status

from .knowledge import KnowledgeDto


class SimpleQAUsecase:
    def __init__(self, qa_service: QAServiceIF):
        self.__qa_service = qa_service

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def execute(self, question: Question) -> Answer:
        try:
            answer = await self.__qa_service.ask(question)
        except Exception as exc:
            self.__handle_error(error=exc, description="Failed to get answer to question")
        return answer


class ContextualQAUsecase:
    def __init__(self, qa_service: QAServiceIF):
        self.__qa_service = qa_service

    def __handle_error(
        self, description: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, error: Exception | None = None
    ):
        raise ConnectorException(status_code=status_code, description=description, upstream_exc=error)

    async def execute(self, question: Question, knowledges: list[KnowledgeDto]) -> Answer:
        try:
            answer = await self.__qa_service.ask(question, knowledges)
        except Exception as exc:
            self.__handle_error(error=exc, description="Failed to get answer to question with context")
        return answer
