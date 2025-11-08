"""Top-level API router."""

from fastapi import APIRouter

from app.api.routes import chat, documents, health, secrets, test_endpoint

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)
api_router.include_router(secrets.router)
api_router.include_router(test_endpoint.router)

