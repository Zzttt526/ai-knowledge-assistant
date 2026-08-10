from pathlib import Path
from uuid import uuid4

import pytest

chromadb = pytest.importorskip("chromadb")

from app.models.document import TextChunk
from app.services.vector_store import VectorStore


def test_add_and_search_documents(tmp_path: Path) -> None:
    store = VectorStore(str(tmp_path / "vectors"), f"test_{uuid4().hex}")
    chunks = [
        TextChunk("annual-leave", "员工享有十天年假", "policy.md"),
        TextChunk("expense", "报销需要提供发票", "finance.md"),
    ]
    store.add_documents(chunks, [[1.0, 0.0], [0.0, 1.0]])

    results = store.search([0.95, 0.05], limit=1)

    assert len(results) == 1
    assert results[0].source_file == "policy.md"
    assert results[0].similarity > 0.9
