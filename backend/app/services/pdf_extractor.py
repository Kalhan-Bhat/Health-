"""Validate an uploaded PDF and extract its text (spec §8.3).

Everything happens in memory: the uploaded bytes are never written to disk and the
extracted text is never logged.
"""

import io
import logging
import re
from dataclasses import dataclass
from typing import Literal

import pdfplumber
import pymupdf as fitz  # PyMuPDF (imported under its classic short name "fitz")
from fastapi import UploadFile

from app.config import get_settings
from app.errors import AppError

logger = logging.getLogger("medbridge.pdf")

PAGE_SEPARATOR = "\n\n--- Page {n} ---\n\n"


@dataclass
class ExtractedPDF:
    text: str  # page texts joined with "\n\n--- Page N ---\n\n"
    pages: int
    method: Literal["pymupdf", "pdfplumber"]


async def read_capped(file: UploadFile, max_mb: int) -> bytes:
    """Read an upload but stop as soon as it goes over the size limit.

    Reading one byte past the limit is enough to know the file is too big, so we never
    hold an unbounded amount of data in memory.
    """
    limit = max_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise AppError(
            "FILE_TOO_LARGE",
            413,
            f"This file is larger than {max_mb} MB. Please upload a smaller PDF.",
            {"max_mb": max_mb},
        )
    return data


def validate_and_extract(
    data: bytes, filename: str | None, content_type: str | None
) -> ExtractedPDF:
    """Check that `data` is a usable text-based PDF and return its text.

    Raises AppError with one of: NO_FILE, FILE_TOO_LARGE, UNSUPPORTED_FILE_TYPE,
    ENCRYPTED_PDF, TOO_MANY_PAGES, SCANNED_PDF_UNSUPPORTED.
    """
    settings = get_settings()

    # 1) Size (also enforced while reading; kept here so the function is safe on its own).
    if not data:
        raise AppError("NO_FILE", 400, "The uploaded file is empty. Please choose a PDF file.")
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise AppError(
            "FILE_TOO_LARGE",
            413,
            f"This file is larger than {settings.MAX_UPLOAD_MB} MB. Please upload a smaller PDF.",
            {"max_mb": settings.MAX_UPLOAD_MB},
        )

    # 2) File type: the extension AND the magic bytes must both say "PDF".
    #    (The browser-supplied MIME type is easy to fake, so it only gets a light check.)
    name_ok = (filename or "").lower().endswith(".pdf")
    magic_ok = data[:5] == b"%PDF-"
    mime_ok = content_type in (None, "", "application/pdf", "application/octet-stream")
    if not (name_ok and magic_ok and mime_ok):
        raise AppError(
            "UNSUPPORTED_FILE_TYPE",
            415,
            "Only PDF files are supported. Please upload your lab report as a PDF.",
        )

    # 3) Open the PDF, check for a password and the page count.
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # a corrupt file that starts with %PDF-
        raise AppError(
            "UNSUPPORTED_FILE_TYPE", 415, "This PDF could not be opened. It may be damaged."
        ) from exc

    with doc:
        if doc.needs_pass:
            raise AppError(
                "ENCRYPTED_PDF",
                422,
                "This PDF is password-protected. Please remove the password and try again.",
            )
        pages = doc.page_count
        if pages > settings.MAX_PDF_PAGES:
            raise AppError(
                "TOO_MANY_PAGES",
                422,
                f"This PDF has {pages} pages. MedBridge accepts up to "
                f"{settings.MAX_PDF_PAGES} pages.",
                {"pages": pages, "max_pages": settings.MAX_PDF_PAGES},
            )

        # 4) Primary extraction with PyMuPDF. sort=True keeps a natural reading order,
        #    which matters for table-style lab reports.
        page_texts = [page.get_text("text", sort=True) for page in doc]

    text = _join_pages(page_texts)
    method: Literal["pymupdf", "pdfplumber"] = "pymupdf"

    # 5) Too little text? Try pdfplumber before giving up.
    # 6) Or the PyMuPDF output looks like a broken table (few lines with numbers)?
    #    Also try pdfplumber and keep whichever has more number-bearing lines.
    too_short = len(text.strip()) < settings.MIN_EXTRACTED_CHARS
    if too_short or _digit_line_ratio(text) < 0.30:
        alt = _extract_with_pdfplumber(data)
        if alt is not None:
            alt_better = _count_digit_lines(alt) > _count_digit_lines(text)
            if (too_short and len(alt.strip()) > len(text.strip())) or alt_better:
                text, method = alt, "pdfplumber"

    if len(text.strip()) < settings.MIN_EXTRACTED_CHARS:
        raise AppError(
            "SCANNED_PDF_UNSUPPORTED",
            422,
            "This PDF looks like a scanned image. MedBridge currently supports "
            "text-based PDFs only.",
        )

    # 7) Clean up and cap the length sent to the LLM.
    text = normalize_text(text)
    truncated = len(text) > settings.MAX_REPORT_CHARS
    if truncated:
        text = text[: settings.MAX_REPORT_CHARS]
    # Log only sizes and the method — never the text itself.
    logger.info(
        "PDF extracted: pages=%d method=%s chars=%d truncated=%s",
        pages,
        method,
        len(text),
        truncated,
    )
    return ExtractedPDF(text=text, pages=pages, method=method)


# ---------------------------------------------------------------- helpers


def _join_pages(page_texts: list[str]) -> str:
    parts = []
    for i, t in enumerate(page_texts, start=1):
        parts.append((PAGE_SEPARATOR.format(n=i) if i > 1 else "") + t)
    return "".join(parts)


def _extract_with_pdfplumber(data: bytes) -> str | None:
    """Fallback extractor. layout=True keeps table columns roughly aligned."""
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return _join_pages([(p.extract_text(layout=True) or "") for p in pdf.pages])
    except Exception:  # pdfplumber is only a fallback; never let it crash the request
        logger.warning("pdfplumber fallback failed")
        return None


def _non_empty_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip()]


def _count_digit_lines(text: str) -> int:
    return sum(1 for ln in _non_empty_lines(text) if any(c.isdigit() for c in ln))


def _digit_line_ratio(text: str) -> float:
    lines = _non_empty_lines(text)
    return _count_digit_lines(text) / len(lines) if lines else 0.0


def normalize_text(text: str) -> str:
    """Strip null bytes, tidy spaces, and collapse runs of blank lines."""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse long runs of spaces/tabs (from layout mode) but keep a 2-space gap so
    # table columns stay visually separate for the LLM.
    text = re.sub(r"[ \t]{3,}", "  ", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
