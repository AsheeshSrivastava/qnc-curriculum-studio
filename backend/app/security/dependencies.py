"""FastAPI dependencies exposing secret storage."""

from __future__ import annotations

from app.security.secret_store import SecretStore, get_secret_store


def get_secret_store_dependency() -> SecretStore:
    return get_secret_store()




