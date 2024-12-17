from collections.abc import AsyncGenerator

from ddd.domains.qa import Answer
from pydantic import BaseModel, ConfigDict, Field


class QuestionRequest(BaseModel):
    model: str = Field(description="回答生成に利用するモデル名", examples=["llama3.2"])
    text: str = Field(description="質問文", examples=["Why is the sky blue?"])


class AnswerChunkResponse(BaseModel):
    model: str = Field(description="回答生成に利用するモデル名", examples=["llama3.2"])
    text: str = Field(description="回答文", examples=["The sky is blue because it is the color of the sky."])


class AnswerResponse(BaseModel):
    content: AsyncGenerator[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    async def content_dump(content: AsyncGenerator[AnswerChunkResponse]) -> AsyncGenerator[str]:
        async for chunk in content:
            yield chunk.model_dump_json() + "\n"

    @staticmethod
    def from_entity(answer: Answer) -> "AnswerResponse":
        return AnswerResponse(content=AnswerResponse.content_dump(answer.content))
