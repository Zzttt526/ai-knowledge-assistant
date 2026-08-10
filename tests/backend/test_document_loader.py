from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.services.document_loader import DocumentLoader, DocumentProcessingError


def test_extracts_utf8_markdown(tmp_path: Path) -> None:
    source = tmp_path / "policy.md"
    source.write_text("# 年假\n员工享有 10 天年假。", encoding="utf-8")

    text = DocumentLoader(Settings(upload_dir=str(tmp_path))).extract_text(source)

    assert "10 天年假" in text


def test_rejects_unsupported_extension(tmp_path: Path) -> None:
    source = tmp_path / "malware.exe"
    source.write_text("data", encoding="utf-8")

    with pytest.raises(DocumentProcessingError, match="不支持"):
        DocumentLoader(Settings(upload_dir=str(tmp_path))).extract_text(source)


def test_upload_endpoint_persists_and_returns_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.routes import documents
    from app.api.dependencies import current_user
    from app.main import app

    class StubEmbeddingService:
        def __init__(self, *_args: object) -> None:
            pass

        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0] for _ in texts]

    class StubVectorStore:
        def __init__(self, *_args: object) -> None:
            pass

        def add_documents(self, chunks: list[object], embeddings: list[object]) -> None:
            assert len(chunks) == len(embeddings)

    monkeypatch.setattr(documents, "EmbeddingService", StubEmbeddingService)
    monkeypatch.setattr(documents, "VectorStore", StubVectorStore)
    app.dependency_overrides[documents.get_settings] = lambda: Settings(
        upload_dir=str(tmp_path / "uploads"), vector_db_path=str(tmp_path / "vectors")
    )
    app.dependency_overrides[current_user] = lambda: "system"
    try:
        response = TestClient(app).post(
            "/api/v1/documents/upload",
            files={"file": ("leave-policy.md", "员工享有十天年假", "text/markdown")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "leave-policy.md"
    assert body["text_length"] == len("员工享有十天年假")
    assert body["status"] == "processed"
