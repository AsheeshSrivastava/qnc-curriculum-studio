"""Pydantic models for ingestion endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    source_type: Literal["pdf", "markdown", "json", "text"]
    source_uri: str | None
    created_at: datetime
    updated_at: datetime


class IngestionResponse(BaseModel):
    document_id: uuid.UUID = Field(..., description="Persisted document identifier.")
    chunk_count: int = Field(..., ge=1, description="Number of chunks written to the vector store.")




