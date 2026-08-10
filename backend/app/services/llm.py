"""OpenAI-compatible LLM client with an explicit mock mode."""

from __future__ import annotations

from app.core.config import Settings


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def answer(self, question: str, context: str) -> str:
        if self._settings.llm_mode.lower() == "mock":
            return self._mock_answer(context)
        try:
            return self._request_completion(question, context)
        except Exception as exc:
            if self._settings.llm_allow_mock_fallback:
                return f"（真实模型调用失败，已切换 Mock）{self._mock_answer(context)}"
            raise RuntimeError("LLM request failed; check LLM_API_KEY and LLM_BASE_URL") from exc

    def _request_completion(self, question: str, context: str) -> str:
        if not self._settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is required when LLM_MODE is not mock")
        import httpx

        response = httpx.post(
            f"{self._settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {self._settings.llm_api_key}"},
            json={
                "model": self._settings.llm_model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": "Answer only from the supplied knowledge-base context. State when context is insufficient."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if not content:
            raise RuntimeError("LLM returned an empty answer")
        return str(content)

    @staticmethod
    def _mock_answer(context: str) -> str:
        if not context:
            return "知识库中暂未找到与该问题相关的内容。"
        return f"（Mock LLM）根据知识库检索到的内容：\n{context}"
