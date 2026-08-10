from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A searchable fragment derived from one source document."""

    chunk_id: str
    content: str
    source_file: str
    document_id: str | None = None


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    content: str
    source_file: str
    similarity: float
