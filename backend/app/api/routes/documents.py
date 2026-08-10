from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.services.document_loader import DocumentLoader, DocumentProcessingError
from app.services.embedding import EmbeddingService
from app.services.text_splitter import TextSplitter
from app.services.vector_store import VectorStore
from app.services.repository import ApplicationRepository
from app.api.dependencies import current_user

router = APIRouter(prefix="/documents")


class UploadResponse(BaseModel):
    filename: str
    document_id: str
    text_length: int
    status: str


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    text_length: int
    created_at: str


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)
) -> UploadResponse:
    loader = DocumentLoader(settings)
    try:
        document_id, stored_path, text = await loader.save_and_extract(file)
        chunks = TextSplitter(settings.chunk_size, settings.chunk_overlap).split(
            text, file.filename or "", document_id
        )
        embeddings = EmbeddingService(settings.model_name, settings.embedding_allow_fallback).embed_texts(
            [chunk.content for chunk in chunks]
        )
        VectorStore(settings.vector_db_path, settings.vector_collection).add_documents(chunks, embeddings)
        ApplicationRepository(settings.app_database_path).add_document(
            document_id, file.filename or "", str(stored_path), len(text), user_id
        )
    except (DocumentProcessingError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UploadResponse(
        filename=file.filename or "",
        document_id=document_id,
        text_length=len(text),
        status="processed",
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)) -> list[dict[str, object]]:
    return ApplicationRepository(settings.app_database_path).list_documents(user_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, settings: Settings = Depends(get_settings), user_id: str = Depends(current_user)) -> None:
    repository = ApplicationRepository(settings.app_database_path)
    document = repository.get_document(document_id,user_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        VectorStore(settings.vector_db_path, settings.vector_collection).delete_document(document_id)
        stored_path = Path(str(document["stored_path"]))
        stored_path.unlink(missing_ok=True)
        stored_path.parent.rmdir()
        repository.delete_document(document_id)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Failed to delete document file") from exc
