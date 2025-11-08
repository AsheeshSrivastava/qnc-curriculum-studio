"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    app_env: Literal["development", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins for the API.",
    )

    default_provider: Literal["openai", "gemini", "openrouter"] = "openai"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    langchain_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openai_chat_model: str = "gpt-4o-mini"
    gemini_chat_model: str = "models/gemini-1.5-flash-latest"
    openrouter_chat_model: str = "anthropic/claude-3-haiku:beta"
    langsmith_project: Optional[str] = None

    redis_url: Optional[AnyUrl] = Field(
        default=None,
        description="Redis connection URL for caching and transient key storage.",
    )
    database_url: Optional[AnyUrl] = Field(
        default=None, description="SQLAlchemy-style database URL with pgvector enabled."
    )

    secret_key_rotation_days: int = Field(
        default=7, ge=1, description="Rotation cadence for envelope encryption keys."
    )
    chunk_size: int = Field(default=800, ge=100, le=2000)
    chunk_overlap: int = Field(default=200, ge=0, le=400)
    secret_encryption_key: str | None = Field(
        default=None,
        description="Base64 urlsafe 32-byte key used for encrypting provider secrets.",
    )
    secret_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default TTL for stored provider secrets.",
    )
    retrieval_max_distance: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Maximum cosine distance before triggering web search fallback.",
    )
    retrieval_min_results: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Minimum number of vector hits required before triggering web search.",
    )
    metrics_enabled: bool = Field(default=True)
    enable_tracing: bool = Field(default=False)
    otlp_endpoint: str | None = Field(
        default=None,
        description="OTLP endpoint for OpenTelemetry span export (e.g., http://collector:4318/v1/traces).",
    )
    otlp_headers: str | None = Field(
        default=None,
        description="Comma separated key=value header pairs for OTLP exporter authentication.",
    )
    
    # Narrative enrichment settings (Aethelgard Academy)
    enable_narrative_enrichment: bool = Field(
        default=False,
        description="Enable Gemini-powered narrative enrichment for learning experiences.",
    )
    enrichment_quality_threshold: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
        description="Quality score threshold - enrich if score below this value.",
    )
    enrichment_cache_enabled: bool = Field(
        default=True,
        description="Enable caching of enriched responses and templates.",
    )
    
    # Research Engine settings
    research_mode: Literal["quick", "standard", "deep"] = Field(
        default="standard",
        description="Research depth level: quick (15-25s), standard (30-45s), deep (60-90s).",
    )
    always_use_tavily: bool = Field(
        default=True,
        description="Always run Tavily web search in parallel with RAG for comprehensive research.",
    )
    tavily_max_results: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of Tavily search results to retrieve.",
    )
    cache_ttl_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Cache expiration in days for deterministic content generation.",
    )
    technical_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for technical answer generation (lower = more deterministic).",
    )
    narrative_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for narrative enrichment (higher = more creative).",
    )
    
    # Multi-Agent Pipeline settings
    enable_multi_agent_pipeline: bool = Field(
        default=True,
        description="Enable 4-agent pipeline (Classifier → Scenario → Story → Polish).",
    )
    scenario_temperature: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Temperature for scenario architect agent.",
    )
    storyteller_temperature: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Temperature for Chain-of-Thought storyteller agent.",
    )
    
    # Technical Compiler settings
    enable_technical_compiler: bool = Field(
        default=True,
        description="Enable Technical Compiler Agent for PSW-structured content.",
    )
    compiler_quality_threshold: float = Field(
        default=95.0,
        ge=0.0,
        le=100.0,
        description="Quality threshold for Technical Compiler Agent output.",
    )
    compiler_temperature: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Temperature for compiler agent (balanced structure and accuracy).",
    )
    
    # Quality Gate settings (legacy - kept for backward compatibility)
    narrative_quality_threshold: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Narrative quality score threshold (technical preservation critical).",
    )
    aethelgard_quality_threshold: float = Field(
        default=85.0,
        ge=0.0,
        le=100.0,
        description="Aethelgard brand quality threshold (brand voice critical).",
    )
    quality_degradation_tolerance: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="Max quality score drop allowed during enrichment before abort.",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "config/settings.env"),
        env_ignore_empty=True,
        case_sensitive=False,
    )


def get_settings() -> Settings:
    """Return application settings instance (cache disabled for environment variable updates)."""

    return Settings()  # type: ignore[call-arg]

