"""System-level API schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response payload for health checks."""

    status: Literal["ok"] = Field(default="ok")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = Field(default="research-portal-backend")

