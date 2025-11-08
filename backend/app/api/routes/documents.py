"""Document upload and retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.ingestion.parsers import DocumentParser
from app.ingestion.service import DocumentIngestionService, get_ingestion_service
from app.schemas.ingestion import DocumentSummary, IngestionResponse
from app.services.repositories import document_repository

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    *,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    source_uri: str | None = Form(None),
    session: AsyncSession = Depends(get_db_session),
    ingestion_service: DocumentIngestionService = Depends(get_ingestion_service),
) -> IngestionResponse:
    """Upload a document (PDF/Markdown/JSON) for ingestion."""

    parser = DocumentParser()
    parsed = await parser.parse(file, title_override=title)

    try:
        result = await ingestion_service.ingest(
            session,
            parsed,
            description=description,
            source_uri=source_uri,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return IngestionResponse(document_id=result.document_id, chunk_count=result.chunk_count)


@router.get("", response_model=list[DocumentSummary])
async def list_documents(
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentSummary]:
    """Return recently ingested documents."""

    documents = await document_repository.list_documents(session, limit=limit)
    return [
        DocumentSummary(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            source_type=doc.source_type,  # type: ignore[arg-type]
            source_uri=doc.source_uri,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]




