import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.embedding import EmbeddingService
from app.services.rag_service import RAGService
from app.services.llm import LLMService
from app.services.repository import ApplicationRepository
from app.api.dependencies import current_user
from fastapi.responses import StreamingResponse
from app.services.vector_store import VectorStore

router = APIRouter(prefix="/chat")


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


class SourceResponse(BaseModel):
    filename: str
    content: str
    similarity: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    conversation_id: str


class ConversationResponse(BaseModel):
    conversation_id: str
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    role: str
    content: str
    sources_json: str | None = None
    created_at: str


@router.post("/query", response_model=QueryResponse)
def query_knowledge_base(
    payload: QueryRequest, settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)
) -> QueryResponse:
    try:
        repository = ApplicationRepository(settings.app_database_path)
        conversation_id = repository.ensure_conversation(payload.conversation_id, payload.question,user_id)
        rag = RAGService(
            EmbeddingService(settings.model_name, settings.embedding_allow_fallback),
            VectorStore(settings.vector_db_path, settings.vector_collection),
            LLMService(settings),
        )
        answer, sources = rag.query(payload.question)
        repository.add_message(conversation_id, "user", payload.question)
        repository.add_message(conversation_id, "assistant", answer, json.dumps(sources, ensure_ascii=False))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return QueryResponse(answer=answer, sources=sources, conversation_id=conversation_id)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)) -> list[dict[str, object]]:
    return ApplicationRepository(settings.app_database_path).list_conversations(user_id)


@router.get("/conversations/{conversation_id}", response_model=list[MessageResponse])
def get_conversation(conversation_id: str, settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)) -> list[dict[str, object]]:
    return ApplicationRepository(settings.app_database_path).get_messages(conversation_id,user_id)

@router.post("/query/stream")
def stream_query(payload: QueryRequest, settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)) -> StreamingResponse:
    """SSE answer stream; clients receive source metadata before token chunks."""
    repository=ApplicationRepository(settings.app_database_path); conversation_id=repository.ensure_conversation(payload.conversation_id,payload.question,user_id)
    rag=RAGService(EmbeddingService(settings.model_name,settings.embedding_allow_fallback),VectorStore(settings.vector_db_path,settings.vector_collection),LLMService(settings))
    answer,sources=rag.query(payload.question); repository.add_message(conversation_id,"user",payload.question); repository.add_message(conversation_id,"assistant",answer,json.dumps(sources,ensure_ascii=False))
    def events():
        yield f"data: {json.dumps({'type':'sources','sources':sources,'conversation_id':conversation_id},ensure_ascii=False)}\n\n"
        for token in answer.split(" "): yield f"data: {json.dumps({'type':'token','content':token+' '},ensure_ascii=False)}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"
    return StreamingResponse(events(),media_type="text/event-stream")
