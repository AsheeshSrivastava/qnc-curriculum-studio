"""Supabase client initialization for Curriculum Studio."""

import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file (for local development)
# Streamlit secrets take precedence if available
load_dotenv()


def _get_config_value(key: str, default: str = "") -> str:
    """
    Get configuration value from Streamlit secrets or environment variables.
    Streamlit secrets take precedence.
    """
    # Try Streamlit secrets first (for Streamlit Cloud/local secrets.toml)
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    # Fall back to environment variables (for .env file or system env)
    return os.getenv(key, default)


@st.cache_resource
def get_supabase_client() -> Client:
    """Get cached Supabase client instance."""
    supabase_url = _get_config_value("SUPABASE_URL", "https://rqhpxwlsrgbxsqgpmolc.supabase.co")
    supabase_key = _get_config_value("SUPABASE_ANON_KEY", "")
    
    if not supabase_key:
        raise ValueError(
            "SUPABASE_ANON_KEY is required. "
            "Set it in Streamlit secrets (.streamlit/secrets.toml) or environment variables."
        )
    
    return create_client(supabase_url, supabase_key)


@st.cache_resource
def get_supabase_admin_client() -> Client:
    """Get Supabase admin client for admin operations."""
    supabase_url = _get_config_value("SUPABASE_URL", "https://rqhpxwlsrgbxsqgpmolc.supabase.co")
    supabase_service_key = _get_config_value("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not supabase_service_key:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY is required for admin operations. "
            "Set it in Streamlit secrets (.streamlit/secrets.toml) or environment variables."
        )
    
    return create_client(supabase_url, supabase_service_key)

