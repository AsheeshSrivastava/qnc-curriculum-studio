"""Encrypted secret storage backed by Redis."""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.security.crypto import EnvelopeCipher

logger = get_logger(__name__)


@dataclass(slots=True)
class StoredSecret:
    """Metadata returned when retrieving a secret."""

    provider: str
    secret: str
    created_at: float
    expires_at: float
    fingerprint: str


class SecretStore:
    """Encrypt secrets and persist them with TTL in Redis."""

    def __init__(
        self,
        *,
        redis_client: Optional[redis.Redis] = None,
        cipher: Optional[EnvelopeCipher] = None,
        default_ttl: Optional[int] = None,
    ) -> None:
        self._redis = redis_client or get_redis()
        self._cipher = cipher or EnvelopeCipher.from_config()
        settings = get_settings()
        self._default_ttl = default_ttl or settings.secret_ttl_seconds

    async def store_secret(self, provider: str, secret: str, *, ttl: Optional[int] = None) -> str:
        token = self._fresh_token()
        ttl_seconds = ttl or self._default_ttl
        now = time.time()
        payload = {
            "provider": provider,
            "ciphertext": self._cipher.encrypt(secret.encode("utf-8")).decode("utf-8"),
            "created_at": now,
            "expires_at": now + ttl_seconds,
            "fingerprint": self._fingerprint(secret),
        }
        key = self._redis_key(token)

        await self._redis.set(
            key,
            json.dumps(payload).encode("utf-8"),
            ex=ttl_seconds,
        )
        logger.info("secret.store", provider=provider, token=token[:6] + "***")
        return token

    async def retrieve_secret(self, token: str) -> StoredSecret | None:
        key = self._redis_key(token)
        raw = await self._redis.get(key)
        if raw is None:
            return None

        payload = json.loads(raw.decode("utf-8"))
        plaintext = self._cipher.decrypt(payload["ciphertext"].encode("utf-8")).decode("utf-8")
        return StoredSecret(
            provider=payload["provider"],
            secret=plaintext,
            created_at=payload["created_at"],
            expires_at=payload["expires_at"],
            fingerprint=payload["fingerprint"],
        )

    async def delete_secret(self, token: str) -> None:
        key = self._redis_key(token)
        await self._redis.delete(key)
        logger.info("secret.delete", token=token[:6] + "***")

    async def extend_secret(self, token: str, *, ttl: Optional[int] = None) -> bool:
        key = self._redis_key(token)
        ttl_seconds = ttl or self._default_ttl
        success = await self._redis.expire(key, ttl_seconds)
        return bool(success)

    def _fresh_token(self) -> str:
        return secrets.token_urlsafe(32)

    def _redis_key(self, token: str) -> str:
        return f"portal:secrets:{token}"

    def _fingerprint(self, secret: str) -> str:
        # Use only first 12 chars of SHA256 as fingerprint; intentionally not reversible.
        import hashlib

        return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]


def get_secret_store() -> SecretStore:
    return SecretStore()




