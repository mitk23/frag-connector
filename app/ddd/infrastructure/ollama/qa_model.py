from typing import Literal

import ollama
from ddd.domains.qa import Question
from pydantic import BaseModel


class OllamaQuestionMessage(BaseModel):
    content: str
    role: Literal["user", "system"] | None = "user"

    def to_ollama_message(self) -> ollama.Message:
        return ollama.Message(role=self.role, content=self.content)

    @staticmethod
    def from_question(question: Question) -> "OllamaQuestionMessage":
        return OllamaQuestionMessage(content=question.text, role="user")
