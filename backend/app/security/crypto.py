"""Symmetric encryption helpers for secret storage."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _ensure_key(key: str | None) -> bytes:
    if not key:
        raise RuntimeError("SECRET_ENCRYPTION_KEY must be configured for secure storage.")

    try:
        # Validate by attempting to decode; return original encoded bytes for Fernet usage.
        base64.urlsafe_b64decode(key.encode("utf-8"))
        return key.encode("utf-8")
    except Exception as exc:
        raise RuntimeError("SECRET_ENCRYPTION_KEY must be valid url-safe base64.") from exc


def generate_fernet_key() -> str:
    """Create a random Fernet-compatible key (urlsafe base64)."""

    return base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")


@dataclass(slots=True)
class EnvelopeCipher:
    """Wrapper around Fernet to encrypt/decrypt payloads."""

    fernet: Fernet

    @classmethod
    def from_config(cls) -> "EnvelopeCipher":
        settings = get_settings()
        key_bytes = _ensure_key(settings.secret_encryption_key)
        fernet = Fernet(key_bytes)
        return cls(fernet=fernet)

    def encrypt(self, plaintext: bytes) -> bytes:
        return self.fernet.encrypt(plaintext)

    def decrypt(self, token: bytes) -> bytes:
        try:
            return self.fernet.decrypt(token)
        except InvalidToken as exc:
            raise ValueError("Invalid secret token provided.") from exc

