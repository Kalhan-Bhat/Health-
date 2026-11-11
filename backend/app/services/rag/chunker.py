"""Split knowledge-base markdown files into chunks for embedding (spec §10.3).

Each `## Section` becomes one chunk. Long sections are split on paragraph boundaries
with a small overlap. The title, section and aliases are added to the text we embed,
so short queries like "hb" or "ldl" still find the right document.
"""

from dataclasses import asdict, dataclass
from pathlib import Path

CHARS_PER_TOKEN = 4  # rough rule of thumb for English text


@dataclass
class Chunk:
    chunk_id: str
    doc_slug: str
    title: str
    section: str
    category: str
    source_name: str
    source_url: str | None
    text: str  # the section text shown to users and to the LLM
    embed_text: str  # title + section + aliases + text, used only for embedding

    def to_dict(self) -> dict:
        return asdict(self)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Tiny parser for the `---` block at the top of each file.

    Supports `key: value` and `key: [a, b, c]` lists, which is all the template uses.
    Returns (metadata, body).
    """
    meta: dict = {}
    text = raw.lstrip("﻿")
    if not text.startswith("---"):
        return meta, text
    _, block, body = text.split("---", 2)
    for line in block.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value
    return meta, body


def split_sections(body: str) -> list[tuple[str, str]]:
    """Return [(section heading, section text), ...] using `## ` headings."""
    sections: list[tuple[str, str]] = []
    heading = "Overview"
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if "".join(lines).strip():
                sections.append((heading, "\n".join(lines).strip()))
            heading, lines = line[3:].strip(), []
        else:
            lines.append(line)
    if "".join(lines).strip():
        sections.append((heading, "\n".join(lines).strip()))
    return sections


def split_long_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Split text on blank lines so each piece is at most ~max_chars.

    The last paragraph of a piece is repeated at the start of the next one (up to
    `overlap_chars`) so that context is not lost at the boundary.
    """
    if len(text) <= max_chars:
        return [text]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    pieces: list[str] = []
    current: list[str] = []
    for para in paragraphs:
        if current and len("\n\n".join(current + [para])) > max_chars:
            pieces.append("\n\n".join(current))
            tail = current[-1]
            current = [tail[-overlap_chars:]] if overlap_chars else []
        current.append(para)
    if current:
        pieces.append("\n\n".join(current))
    return pieces


def chunk_file(path: Path, chunk_size_tokens: int, overlap_tokens: int) -> list[Chunk]:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    slug = path.stem
    title = meta.get("title", slug)
    aliases = meta.get("aliases", [])
    alias_text = ", ".join(aliases) if isinstance(aliases, list) else str(aliases)

    chunks: list[Chunk] = []
    for section, text in split_sections(body):
        for piece in split_long_text(
            text, chunk_size_tokens * CHARS_PER_TOKEN, overlap_tokens * CHARS_PER_TOKEN
        ):
            chunks.append(
                Chunk(
                    chunk_id=f"{slug}#{len(chunks)}",
                    doc_slug=slug,
                    title=title,
                    section=section,
                    category=meta.get("category", ""),
                    source_name=meta.get("source_name", "MedBridge knowledge base"),
                    source_url=meta.get("source_url") or None,
                    text=piece,
                    embed_text=f"{title} — {section}\nAliases: {alias_text}\n\n{piece}",
                )
            )
    return chunks


def chunk_directory(kb_dir: Path, chunk_size_tokens: int, overlap_tokens: int) -> list[Chunk]:
    """Chunk every .md file under kb_dir (sorted, so the index is reproducible)."""
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.rglob("*.md")):
        chunks.extend(chunk_file(path, chunk_size_tokens, overlap_tokens))
    return chunks
