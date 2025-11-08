"""API endpoints for secure secret storage."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.providers.base import ProviderName
from app.security.dependencies import get_secret_store_dependency
from app.security.secret_store import SecretStore

logger = get_logger(__name__)

router = APIRouter(prefix="/secrets", tags=["secrets"])


class StoreSecretRequest(BaseModel):
    """Request to store an API key securely."""

    provider: ProviderName
    api_key: str = Field(..., min_length=10)
    ttl_seconds: Optional[int] = Field(default=3600, ge=60, le=86400)


class StoreSecretResponse(BaseModel):
    """Response containing the secret token."""

    token: str
    provider: str
    expires_in: int


@router.post("", response_model=StoreSecretResponse, status_code=status.HTTP_201_CREATED)
async def store_secret(
    request: StoreSecretRequest,
    secret_store: SecretStore = Depends(get_secret_store_dependency),
) -> StoreSecretResponse:
    """
    Store an API key securely and return a token.

    The API key is encrypted and stored in Redis with a TTL.
    The returned token can be used to retrieve the key for API calls.
    """
    try:
        token = await secret_store.store_secret(
            provider=request.provider,
            secret=request.api_key,
            ttl=request.ttl_seconds,
        )

        logger.info(
            "secret.stored",
            provider=request.provider,
            ttl=request.ttl_seconds,
        )

        return StoreSecretResponse(
            token=token,
            provider=request.provider,
            expires_in=request.ttl_seconds or 3600,
        )
    except Exception as e:
        logger.error("secret.store_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store secret: {str(e)}",
        )




