from app.services.text_splitter import TextSplitter


def test_split_creates_overlapping_chunks_with_source() -> None:
    splitter = TextSplitter(chunk_size=20, chunk_overlap=5)
    chunks = splitter.split("one two three four five six seven eight nine", "guide.txt")

    assert len(chunks) > 1
    assert all(chunk.chunk_id for chunk in chunks)
    assert all(chunk.source_file == "guide.txt" for chunk in chunks)
    assert chunks[0].content[-5:].strip() in chunks[1].content
