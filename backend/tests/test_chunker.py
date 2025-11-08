from app.ingestion.chunker import DocumentChunker


def test_document_chunker_splits_text():
    text = "print('hello world')\n" * 50
    chunker = DocumentChunker(chunk_size=80, chunk_overlap=20)
    chunks = chunker.split_text(text)

    assert len(chunks) >= 2
    assert chunks[0].content.strip().startswith("print")
    assert chunks[0].token_count > 0




