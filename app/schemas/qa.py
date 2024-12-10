from collections.abc import AsyncGenerator

from ddd.domains.qa import Answer, AnswerChunk
from pydantic import BaseModel, ConfigDict


class QuestionRequest(BaseModel):
    model: str
    text: str


class AnswerResponse(BaseModel):
    content: AsyncGenerator[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    async def content_dump(content: AsyncGenerator[AnswerChunk]) -> AsyncGenerator[str]:
        async for chunk in content:
            yield chunk.model_dump_json() + "\n"

    @staticmethod
    def from_entity(answer: Answer) -> "AnswerResponse":
        return AnswerResponse(content=AnswerResponse.content_dump(answer.content))
