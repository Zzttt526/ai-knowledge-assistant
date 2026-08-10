"""Text chunking with overlap for retrieval."""

from __future__ import annotations

from uuid import uuid4

from app.models.document import TextChunk


class TextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80) -> None:
        if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_size 必须大于 0，chunk_overlap 必须小于 chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str, source_file: str, document_id: str | None = None) -> list[TextChunk]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[TextChunk] = []
        start = 0
        length = len(normalized)
        while start < length:
            end = min(start + self.chunk_size, length)
            if end < length:
                boundary = normalized.rfind(" ", start, end)
                if boundary > start:
                    end = boundary
            content = normalized[start:end].strip()
            if content:
                chunks.append(TextChunk(str(uuid4()), content, source_file, document_id))
            if end >= length:
                break
            start = max(end - self.chunk_overlap, start + 1)
        return chunks
