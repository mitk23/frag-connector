import abc
from collections.abc import AsyncGenerator

from pydantic import BaseModel, ConfigDict


class Question(BaseModel):
    model: str
    text: str


class AnswerChunk(BaseModel):
    model: str
    text: str


class Answer(BaseModel):
    content: AsyncGenerator[AnswerChunk]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class QAServiceIF(abc.ABC):
    @abc.abstractmethod
    async def ask(self, question: Question) -> Answer:
        raise NotImplementedError
