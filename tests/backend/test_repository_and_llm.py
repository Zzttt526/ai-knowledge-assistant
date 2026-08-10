from pathlib import Path

from app.core.config import Settings
from app.services.llm import LLMService
from app.services.repository import ApplicationRepository


def test_document_and_conversation_history_are_persisted(tmp_path: Path) -> None:
    repository = ApplicationRepository(str(tmp_path / "app.db"))
    repository.add_document("doc-1", "policy.md", "uploads/doc-1/policy.md", 12)
    conversation_id = repository.ensure_conversation(None, "年假有几天？")
    repository.add_message(conversation_id, "user", "年假有几天？")
    repository.add_message(conversation_id, "assistant", "十天", "[]")

    assert repository.list_documents()[0]["filename"] == "policy.md"
    assert repository.list_conversations()[0]["conversation_id"] == conversation_id
    assert [message["role"] for message in repository.get_messages(conversation_id)] == ["user", "assistant"]


def test_real_llm_mode_falls_back_to_mock_without_api_key() -> None:
    answer = LLMService(Settings(llm_mode="real", llm_api_key=None, llm_allow_mock_fallback=True)).answer(
        "问题", "这是知识库内容"
    )

    assert "Mock" in answer
    assert "知识库内容" in answer
