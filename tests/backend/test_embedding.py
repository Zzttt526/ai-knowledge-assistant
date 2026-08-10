from app.services.embedding import EmbeddingService


def test_fallback_embedding_is_deterministic_and_normalized() -> None:
    service = EmbeddingService("not-a-real-model", allow_fallback=True)

    first = service.embed_query("公司年假政策")
    second = service.embed_query("公司年假政策")

    assert len(first) == 384
    assert first == second
    assert round(sum(value * value for value in first), 6) == 1.0
