"""Provider factory for chat models."""

from __future__ import annotations

from typing import Optional

from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.providers.base import (
    ProviderConfigurationError,
    ProviderCredentials,
    ProviderName,
    ProviderSettings,
)
from app.providers.gemini import GeminiChatModel
from app.security.secret_store import SecretStore


async def resolve_credentials(
    provider: ProviderName,
    *,
    secret_store: SecretStore,
    secret_token: Optional[str],
) -> ProviderCredentials:
    """Return API credentials from environment variables (simplified for production)."""

    settings = get_settings()

    # Always use environment variables for simplicity and reliability
    if provider == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured in environment.")
        return ProviderCredentials(api_key=settings.openai_api_key, source="environment")
    if provider == "gemini":
        if not settings.google_api_key:
            raise ProviderConfigurationError("GOOGLE_API_KEY is not configured in environment.")
        return ProviderCredentials(api_key=settings.google_api_key, source="environment")
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ProviderConfigurationError("OPENROUTER_API_KEY is not configured in environment.")
        return ProviderCredentials(api_key=settings.openrouter_api_key, source="environment")

    raise ProviderConfigurationError(f"Unsupported provider '{provider}'.")


def resolve_settings(provider: ProviderName) -> ProviderSettings:
    """Return model configuration for the provider."""

    settings = get_settings()

    if provider == "openai":
        return ProviderSettings(
            name=provider,
            model=settings.openai_chat_model,
            temperature=0.1,
        )
    if provider == "gemini":
        return ProviderSettings(
            name=provider,
            model=settings.gemini_chat_model,
            temperature=0.1,
        )
    if provider == "openrouter":
        return ProviderSettings(
            name=provider,
            model=settings.openrouter_chat_model,
            base_url=settings.openrouter_base_url,
            temperature=0.1,
        )

    raise ProviderConfigurationError(f"Unsupported provider '{provider}'.")


async def get_chat_model(
    provider: ProviderName,
    *,
    secret_store: SecretStore,
    secret_token: Optional[str],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
):
    """Instantiate a LangChain chat model for the provider.
    
    Args:
        provider: The LLM provider to use
        secret_store: Store for API credentials
        secret_token: Optional token for user-supplied credentials
        model: Optional model override (defaults to provider_settings.model)
        temperature: Optional temperature override (defaults to provider_settings.temperature)
    """

    provider_settings = resolve_settings(provider)
    credentials = await resolve_credentials(provider, secret_store=secret_store, secret_token=secret_token)

    # Use overrides if provided, otherwise use provider settings
    final_model = model or provider_settings.model
    final_temperature = temperature if temperature is not None else provider_settings.temperature

    if provider == "openai":
        return ChatOpenAI(
            model=final_model,
            api_key=credentials.api_key,
            temperature=final_temperature,
        )
    if provider == "gemini":
        return GeminiChatModel(
            model=final_model,
            api_key=credentials.api_key,
            temperature=final_temperature,
        )
    if provider == "openrouter":
        return ChatOpenAI(
            model=final_model,
            api_key=credentials.api_key,
            base_url=provider_settings.base_url,
            temperature=final_temperature,
        )

    raise ProviderConfigurationError(f"Unsupported provider '{provider}'.")

