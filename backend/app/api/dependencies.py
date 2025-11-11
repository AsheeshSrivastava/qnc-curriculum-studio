"""FastAPI dependencies for authentication and authorization."""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Header, status
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def verify_supabase_jwt(
    authorization: Optional[str] = Header(None, description="Bearer token from Supabase Auth")
) -> Dict[str, Any]:
    """
    Verify Supabase JWT token from Authorization header.
    Accepts tokens from BOTH Curriculum Studio and Aethelgard Supabase projects.
    
    Returns decoded user info if valid from either project.
    Raises HTTPException if invalid or missing.
    """
    if not authorization:
        logger.warning("auth.missing_header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        logger.warning("auth.invalid_format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    settings = get_settings()
    
    # Try Curriculum Studio first
    if settings.supabase_curriculum_url and settings.supabase_curriculum_key:
        try:
            from supabase import create_client
            
            curriculum_client = create_client(
                settings.supabase_curriculum_url,
                settings.supabase_curriculum_key
            )
            user_response = curriculum_client.auth.get_user(token)
            
            if user_response and user_response.user:
                user = user_response.user
                logger.info(
                    "auth.success",
                    source="curriculum_studio",
                    user_id=user.id,
                    user_email=user.email
                )
                return {
                    "user_id": user.id,
                    "email": user.email,
                    "source": "curriculum_studio",
                    "user": user,
                }
        except Exception as e:
            logger.debug("auth.curriculum_failed", error=str(e))
            # Continue to try Aethelgard
    
    # Try Aethelgard second
    if settings.supabase_aethelgard_url and settings.supabase_aethelgard_key:
        try:
            from supabase import create_client
            
            aethelgard_client = create_client(
                settings.supabase_aethelgard_url,
                settings.supabase_aethelgard_key
            )
            user_response = aethelgard_client.auth.get_user(token)
            
            if user_response and user_response.user:
                user = user_response.user
                logger.info(
                    "auth.success",
                    source="aethelgard",
                    user_id=user.id,
                    user_email=user.email
                )
                return {
                    "user_id": user.id,
                    "email": user.email,
                    "source": "aethelgard",
                    "user": user,
                }
        except Exception as e:
            logger.debug("auth.aethelgard_failed", error=str(e))
            # Continue to final error
    
    # Neither worked
    logger.warning("auth.invalid_token", token_prefix=token[:10] if len(token) > 10 else token)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    auth_data: Dict[str, Any] = Depends(verify_supabase_jwt)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user.
    Use this in protected endpoints.
    """
    return auth_data

