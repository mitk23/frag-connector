import textwrap

from ddd.domains.frag import FederatedRAGQueryContent, RetrievalParams
from ddd.domains.qa import Question
from pydantic import BaseModel

from .knowledge import FederatedKnowledgeQueryDto, KnowledgeQueryConfigDto, KnowledgeQueryDto


class FederatedRetrievalConfigDto(BaseModel):
    retrieval_params: RetrievalParams
    retrieval_providers: list[str]
    number_of_knowledges: int
    rerank_knowledges_by: str

    def to_knowledge_query_config(self) -> KnowledgeQueryConfigDto:
        return KnowledgeQueryConfigDto(
            top_k=self.retrieval_params.top_k,
            filter=self.retrieval_params.filter,
            exact_search=self.retrieval_params.exact_search,
        )


class GenerationConfigDto(BaseModel):
    llm_provider: str
    llm_model: str


class FederatedRAGQueryDto(BaseModel):
    query: FederatedRAGQueryContent
    retrieval: FederatedRetrievalConfigDto
    generation: GenerationConfigDto

    def to_retrieval_query(self) -> FederatedKnowledgeQueryDto:
        query_config = self.retrieval.to_knowledge_query_config()
        query = KnowledgeQueryDto(text=self.query.text, embedding=self.query.embedding, config=query_config)

        return FederatedKnowledgeQueryDto(
            query=query,
            providers=self.retrieval.retrieval_providers,
            knowledge_rerank_method=self.retrieval.rerank_knowledges_by,
            return_num_knowledges=self.retrieval.number_of_knowledges,
        )

    def to_prompt(self, knowledges: FederatedKnowledgeQueryDto) -> Question:
        question_text = self.query.text
        knowledge_text = "\n\n".join([knowledge.text for knowledge in knowledges])

        prompt = textwrap.dedent(f"""\
            Context information is below.
            ---------------------
            {knowledge_text}
            ---------------------
            Given the context information, answer the query.
            Query: {question_text}
            Answer:
        """)

        return Question(model=self.generation.llm_model, text=prompt)
