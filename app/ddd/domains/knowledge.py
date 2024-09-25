import abc
from typing import Any, Generator

from core.exceptions import InternalException
from pydantic import BaseModel


class Knowledge(BaseModel):
    id: str | None = None
    text: str | None = None
    embedding: list[float] | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None

    def __eq__(self, obj: object) -> bool:
        return self.id == obj.id


class KnowledgeQueryConfig(BaseModel):
    top_k: int | None = 3
    include_embedding: bool | None = True
    include_metadata: bool | None = True
    filter: dict[str, Any] | None = None


class KnowledgeQuery(BaseModel):
    text: str | None = None
    embedding: list[float] | None = None
    config: KnowledgeQueryConfig | None = KnowledgeQueryConfig()


class KnowledgeQueryServiceIF(abc.ABC):
    @abc.abstractmethod
    async def query(self, query: KnowledgeQuery) -> list[Knowledge]:
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch(self, knowledge_id_list: list[str]) -> list[Knowledge]:
        raise NotImplementedError

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)


class Question(BaseModel):
    text: str


class Answer(BaseModel):
    text: Generator[str, None, None]


class QAServiceIF(abc.ABC):
    @abc.abstractmethod
    async def ask(self, question: Question, knowledges: list[Knowledge] | None) -> Answer:
        raise NotImplementedError


# class LLMQuery(BaseModel):
#     model: str
#     user_prompt: str
#     system_prompt: str | None = None
