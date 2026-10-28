import pytest

from app.utils.text_utils import clean_text, split_text


def test_clean_text_removes_null_bytes_and_extra_space():
    result = clean_text("Hello\x00   world\n\n\n\nNext")
    assert "\x00" not in result
    assert "Hello world" in result
    assert "\n\n\n" not in result


def test_split_text_empty_returns_no_chunks():
    assert split_text("   ", 200, 50) == []


def test_short_text_is_one_chunk():
    assert split_text("small text", 200, 50) == ["small text"]


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"word{i}" for i in range(300))
    chunks = split_text(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)

    # Each chunk starts with text that also appears at the end of the previous one
    for previous, current in zip(chunks, chunks[1:]):
        assert current[:10] in previous

    # Nothing is lost at the start or the end
    assert chunks[0].startswith("word0")
    assert chunks[-1].endswith("word299")


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        split_text("some text", chunk_size=100, overlap=100)