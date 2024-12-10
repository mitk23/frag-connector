import abc
import textwrap
from collections.abc import AsyncGenerator

from pydantic import BaseModel, ConfigDict

from .knowledge import Knowledge


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

    @staticmethod
    def generate_prompt(question: Question, knowledges: list[Knowledge] | None) -> str:
        if knowledges is None:
            return question.text

        knowledge_text = "\n\n".join([knowledge.text for knowledge in knowledges])

        prompt = textwrap.dedent(f"""\
            Context information is below.
            ---------------------
            {knowledge_text}
            ---------------------
            Given the context information, answer the query.
            Query: {question.text}
            Answer:
        """)
        return prompt
