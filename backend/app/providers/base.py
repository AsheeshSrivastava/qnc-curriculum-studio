"""Common provider definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

ProviderName = Literal["openai", "gemini", "openrouter"]


class ProviderConfigurationError(RuntimeError):
    """Raised when provider-specific configuration is missing or invalid."""


@dataclass(slots=True)
class ProviderSettings:
    """Resolved configuration for a provider."""

    name: ProviderName
    model: str
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None


@dataclass(slots=True)
class ProviderCredentials:
    """Resolved credentials for instantiating an LLM provider."""

    api_key: str
    source: Literal["default", "user"]




