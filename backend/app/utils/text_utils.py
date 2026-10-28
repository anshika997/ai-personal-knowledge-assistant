import re


def clean_text(text: str) -> str:
    """Remove bad characters and extra blank spaces."""
    text = text.replace("\x00", "")        # PostgreSQL cannot store null bytes
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)    # many spaces -> one space
    text = re.sub(r"\n{3,}", "\n\n", text) # many blank lines -> one blank line
    return text.strip()


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into chunks of about `chunk_size` characters.
    Each chunk repeats the last `overlap` characters of the previous one.
    """
    if overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")

    text = text.strip()
    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)

        # Try to cut at a space so we do not break a word in the middle
        if end < length:
            cut = text.rfind(" ", start + int(chunk_size * 0.6), end)
            if cut != -1:
                end = cut

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= length:
            break

        # Move forward, but go back a little to create the overlap
        start = max(end - overlap, start + 1)

    return chunks