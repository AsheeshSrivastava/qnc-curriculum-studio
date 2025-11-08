"""API client for backend communication."""

import os
from typing import Any, Optional

import requests
import streamlit as st


class APIClient:
    """Client for interacting with the Research Portal backend API."""

    def __init__(self, base_url: Optional[str] = None):
        """Initialize API client with base URL."""
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
        self.session = requests.Session()

    def health_check(self) -> dict[str, Any]:
        """Check backend health status."""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Backend connection failed: {e}")
            return {"status": "error", "message": str(e)}

    def upload_document(
        self,
        file_content: bytes,
        filename: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Upload and ingest a document."""
        try:
            files = {"file": (filename, file_content)}
            data = {}
            if title:
                data["title"] = title
            if description:
                data["description"] = description

            response = self.session.post(
                f"{self.base_url}/api/documents",
                files=files,
                data=data,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
            raise Exception(f"Upload failed: {error_detail}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")

    def list_documents(self, limit: int = 20) -> list[dict[str, Any]]:
        """List ingested documents."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/documents",
                params={"limit": limit},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to fetch documents: {e}")
            return []

    def chat_query(
        self,
        question: str,
        provider: str = "openai",
        secret_token: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        stream: bool = False,
    ) -> dict[str, Any] | requests.Response:
        """Send a chat query to the backend."""
        try:
            payload = {
                "question": question,
                "provider": provider,
                "secret_token": secret_token,
                "history": history or [],
            }

            if stream:
                response = self.session.post(
                    f"{self.base_url}/api/chat/query",
                    json=payload,
                    params={"stream": "true"},
                    stream=True,
                    timeout=120,
                )
                response.raise_for_status()
                return response
            else:
                response = self.session.post(
                    f"{self.base_url}/api/chat/query",
                    json=payload,
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
            raise Exception(f"Chat query failed: {error_detail}")
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")

    def export_chat(
        self,
        question: str,
        answer: str,
        citations: list[dict[str, Any]],
        evaluation: dict[str, Any],
        format: str = "markdown",
    ) -> bytes:
        """Export chat conversation to specified format."""
        try:
            payload = {
                "question": question,
                "answer": answer,
                "citations": citations,
                "evaluation": evaluation,
                "format": format,
            }

            response = self.session.post(
                f"{self.base_url}/api/chat/export",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")

    def store_api_key(
        self,
        provider: str,
        api_key: str,
        ttl_seconds: int = 3600,
    ) -> dict[str, Any]:
        """Store an API key securely and get a token."""
        try:
            payload = {
                "provider": provider,
                "api_key": api_key,
                "ttl_seconds": ttl_seconds,
            }

            response = self.session.post(
                f"{self.base_url}/api/secrets",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
            raise Exception(f"Failed to store API key: {error_detail}")
        except Exception as e:
            raise Exception(f"API key storage error: {str(e)}")


@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()

