"""Document parsing utilities for uploads."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from markdown import markdown
from pypdf import PdfReader


@dataclass(slots=True)
class ParsedDocument:
    """Normalized representation of an uploaded document."""

    title: str
    text: str
    source_type: str
    metadata: dict[str, Any]


class DocumentParser:
    """Parser that supports PDF, Markdown, and JSON uploads."""

    async def parse(self, upload: UploadFile, title_override: str | None = None) -> ParsedDocument:
        raw_bytes = await upload.read()
        filename = upload.filename or "document"
        extension = Path(filename).suffix.lower()
        content_type = upload.content_type or ""

        if extension in {".pdf"} or "pdf" in content_type:
            text = self._parse_pdf(raw_bytes)
            source_type = "pdf"
        elif extension in {".md", ".markdown"} or "markdown" in content_type:
            text = self._parse_markdown(raw_bytes)
            source_type = "markdown"
        elif extension in {".json"} or "json" in content_type:
            text = self._parse_json(raw_bytes)
            source_type = "json"
        else:
            # Fallback: treat as UTF-8 text.
            text = raw_bytes.decode("utf-8", errors="ignore")
            source_type = "text"

        clean_text = self._normalize_whitespace(text)
        metadata = {
            "original_filename": filename,
            "content_type": content_type,
            "size_bytes": len(raw_bytes),
        }

        return ParsedDocument(
            title=title_override or Path(filename).stem,
            text=clean_text,
            source_type=source_type,
            metadata=metadata,
        )

    def _parse_pdf(self, raw: bytes) -> str:
        reader = PdfReader(BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    def _parse_markdown(self, raw: bytes) -> str:
        text = raw.decode("utf-8", errors="ignore")
        # Convert markdown to HTML then strip tags to obtain readable text.
        html = markdown(text)
        stripped = re.sub(r"<[^>]+>", " ", html)
        return stripped

    def _parse_json(self, raw: bytes) -> str:
        payload = json.loads(raw.decode("utf-8", errors="ignore"))
        fragments: list[str] = []
        self._collect_strings(payload, fragments)
        return "\n".join(fragments)

    def _collect_strings(self, node: Any, fragments: list[str]) -> None:
        if isinstance(node, dict):
            for value in node.values():
                self._collect_strings(value, fragments)
        elif isinstance(node, list):
            for item in node:
                self._collect_strings(item, fragments)
        elif isinstance(node, str):
            fragments.append(node)

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

