"""Document chunking and token utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(slots=True)
class TextChunk:
    """Represents a chunk of text ready for embedding."""

    index: int
    content: str
    token_count: int


class DocumentChunker:
    """Chunk documents using LangChain recursive splitter."""

    def __init__(self, *, chunk_size: int, chunk_overlap: int, tokenizer_name: str = "cl100k_base") -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )
        self.encoding = tiktoken.get_encoding(tokenizer_name)

    def split_text(self, text: str) -> list[TextChunk]:
        raw_chunks = self.splitter.split_text(text)
        chunks: list[TextChunk] = []
        for idx, chunk in enumerate(raw_chunks):
            token_count = self.count_tokens(chunk)
            chunks.append(TextChunk(index=idx, content=chunk, token_count=token_count))
        return chunks

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))


def merge_chunks(chunks: Iterable[TextChunk]) -> List[str]:
    """Return raw string contents from chunk objects."""

    return [chunk.content for chunk in chunks]




