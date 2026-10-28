import io

import docx
import pymupdf
import pytest

from app.core.config import settings
from app.services.document_service import extract_pages
from app.utils.file_validation import compute_hash, get_extension, validate_upload


def make_pdf(text: str) -> bytes:
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    data = pdf.tobytes()
    pdf.close()
    return data


def make_docx(text: str) -> bytes:
    document = docx.Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# ---------- validation ----------
def test_valid_file_passes():
    validate_upload("notes.pdf", 1000)   # no error


def test_unsupported_type_is_rejected():
    with pytest.raises(ValueError, match="not supported"):
        validate_upload("virus.exe", 1000)


def test_empty_file_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_upload("notes.txt", 0)


def test_too_large_file_is_rejected():
    too_big = settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1
    with pytest.raises(ValueError, match="too large"):
        validate_upload("notes.txt", too_big)


def test_extension_is_lowercase():
    assert get_extension("REPORT.PDF") == ".pdf"


def test_same_content_gives_same_hash():
    assert compute_hash(b"abc") == compute_hash(b"abc")
    assert compute_hash(b"abc") != compute_hash(b"abd")


# ---------- text extraction ----------
def test_extract_txt():
    assert extract_pages(b"Hello text file", ".txt") == [(None, "Hello text file")]


def test_extract_txt_latin1_fallback():
    pages = extract_pages("café".encode("latin-1"), ".txt")
    assert pages[0][1] == "café"


def test_extract_empty_txt_gives_no_pages():
    assert extract_pages(b"   \n  ", ".txt") == []


def test_extract_docx():
    pages = extract_pages(make_docx("Hello DOCX world"), ".docx")
    assert pages[0][0] is None
    assert "Hello DOCX world" in pages[0][1]


def test_extract_pdf_keeps_page_number():
    pages = extract_pages(make_pdf("Hello PDF world"), ".pdf")
    assert pages[0][0] == 1
    assert "Hello PDF world" in pages[0][1]


def test_broken_pdf_gives_clear_error():
    with pytest.raises(ValueError):
        extract_pages(b"this is not a pdf", ".pdf")