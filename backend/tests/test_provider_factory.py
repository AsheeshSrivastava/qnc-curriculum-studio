import base64
import os

import fakeredis.aioredis
import pytest

from app.core.config import get_settings
from app.providers.factory import ProviderConfigurationError, get_chat_model
from app.security.crypto import EnvelopeCipher
from app.security.secret_store import SecretStore


def _set_secret_key(monkeypatch):
    key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", key)
    monkeypatch.setenv("SECRET_TTL_SECONDS", "120")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_chat_model_openai_default(monkeypatch):
    _set_secret_key(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    get_settings.cache_clear()

    redis_client = fakeredis.aioredis.FakeRedis()
    store = SecretStore(redis_client=redis_client, cipher=EnvelopeCipher.from_config(), default_ttl=120)

    model = await get_chat_model("openai", secret_store=store, secret_token=None)

    assert model.model_name  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_get_chat_model_secret_mismatch(monkeypatch):
    _set_secret_key(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    get_settings.cache_clear()

    redis_client = fakeredis.aioredis.FakeRedis()
    store = SecretStore(redis_client=redis_client, cipher=EnvelopeCipher.from_config(), default_ttl=120)

    token = await store.store_secret("openrouter", "user-key")

    with pytest.raises(ProviderConfigurationError):
        await get_chat_model("openai", secret_store=store, secret_token=token)

