import asyncio
import base64
import os
import time

import fakeredis.aioredis
import pytest

from app.core.config import get_settings
from app.security.crypto import EnvelopeCipher
from app.security.secret_store import SecretStore


def _random_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")


@pytest.mark.asyncio
async def test_store_and_retrieve_secret(monkeypatch):
    redis_client = fakeredis.aioredis.FakeRedis()
    key = _random_key()
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", key)
    monkeypatch.setenv("SECRET_TTL_SECONDS", "120")
    get_settings.cache_clear()

    store = SecretStore(redis_client=redis_client, cipher=EnvelopeCipher.from_config(), default_ttl=120)

    token = await store.store_secret("openai", "sk-test-123")
    assert token

    retrieved = await store.retrieve_secret(token)
    assert retrieved is not None
    assert retrieved.provider == "openai"
    assert retrieved.secret == "sk-test-123"
    assert retrieved.fingerprint
    assert retrieved.expires_at > time.time()

    await store.delete_secret(token)
    assert await store.retrieve_secret(token) is None


@pytest.mark.asyncio
async def test_extend_secret(monkeypatch):
    redis_client = fakeredis.aioredis.FakeRedis()
    key = _random_key()
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", key)
    monkeypatch.setenv("SECRET_TTL_SECONDS", "60")
    get_settings.cache_clear()

    store = SecretStore(redis_client=redis_client, cipher=EnvelopeCipher.from_config(), default_ttl=60)

    token = await store.store_secret("openai", "sk-test-456", ttl=60)
    ttl_before = await redis_client.ttl(store._redis_key(token))  # type: ignore[attr-defined]

    await asyncio.sleep(0.01)
    extended = await store.extend_secret(token, ttl=120)
    ttl_after = await redis_client.ttl(store._redis_key(token))  # type: ignore[attr-defined]

    assert extended is True
    assert ttl_after > ttl_before

