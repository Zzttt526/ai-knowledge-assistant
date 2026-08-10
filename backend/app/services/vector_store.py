"""ChromaDB persistence and similarity search."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from app.models.document import SearchResult, TextChunk


class VectorStore:
    def __init__(self, db_path: str, collection_name: str) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("ChromaDB 未安装，请安装 backend/requirements.txt") from exc

        Path(db_path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=db_path)
        self._collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, chunks: Sequence[TextChunk], embeddings: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks 与 embeddings 数量必须一致")
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=[list(vector) for vector in embeddings],
            metadatas=[
                {"source_file": chunk.source_file, "document_id": chunk.document_id or ""}
                for chunk in chunks
            ],
        )

    def delete_document(self, document_id: str) -> None:
        """Remove every indexed chunk that belongs to a document."""
        self._collection.delete(where={"document_id": document_id})

    def search(self, query_embedding: Sequence[float], limit: int = 4) -> list[SearchResult]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=min(limit, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        return [
            SearchResult(
                chunk_id=chunk_id,
                content=content,
                source_file=metadata["source_file"],
                similarity=round(1 - float(distance), 6),
            )
            for chunk_id, content, metadata, distance in zip(ids, documents, metadatas, distances)
        ]
