from total_recall.rag_core.chunking import chunk_text


def test_chunking_overlap_and_ids() -> None:
    text = " ".join(f"w{i}" for i in range(30))
    chunks = chunk_text(text, "doc.md", chunk_size=10, chunk_overlap=2)
    assert len(chunks) == 4
    assert chunks[0].chunk_id != chunks[1].chunk_id
    assert chunks[0].doc_path == "doc.md"
