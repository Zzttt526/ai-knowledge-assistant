"""Retrieval orchestration and a deliberately simple mock answer generator."""

from __future__ import annotations

from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from app.services.vector_store import VectorStore


class RAGService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore, llm_service: LLMService) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._llm_service = llm_service

    def query(self, question: str) -> tuple[str, list[dict[str, object]]]:
        results = self._vector_store.search(self._embedding_service.embed_query(question))
        sources = [
            {
                "filename": result.source_file,
                "content": result.content,
                "similarity": result.similarity,
            }
            for result in results
        ]
        if not results:
            return self._llm_service.answer(question, ""), sources

        context = "\n\n".join(result.content for result in results)
        answer = self._llm_service.answer(question, context)
        return answer, sources
