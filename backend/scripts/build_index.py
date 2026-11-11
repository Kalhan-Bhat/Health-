"""Build the FAISS index from the knowledge base (spec §10.4).

Run from the backend/ folder:
    python -m scripts.build_index

The first run downloads the embedding model (~90 MB).
"""

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.config import get_settings
from app.services.rag.chunker import chunk_directory
from app.services.rag.embedder import get_embedder
from app.services.rag.index_store import FAISS_AVAILABLE, IndexStore


def kb_content_hash(kb_dir: Path) -> str:
    """Hash of every KB file, so you can tell whether the index is out of date."""
    digest = hashlib.sha256()
    for path in sorted(kb_dir.rglob("*.md")):
        digest.update(path.relative_to(kb_dir).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def build(kb_dir: Path, index_dir: Path, model_name: str, chunk_tokens: int, overlap: int) -> dict:
    chunks = chunk_directory(kb_dir, chunk_tokens, overlap)
    if not chunks:
        raise SystemExit(f"No markdown files found in {kb_dir}")

    vectors = get_embedder(model_name).embed([c.embed_text for c in chunks])
    manifest = {
        "embedding_model": model_name,
        "num_docs": len({c.doc_slug for c in chunks}),
        "num_chunks": len(chunks),
        "dimension": int(vectors.shape[1]),
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "kb_hash": kb_content_hash(kb_dir),
        "faiss_written": FAISS_AVAILABLE,
    }
    IndexStore.save(index_dir, vectors, [c.to_dict() for c in chunks], manifest)
    return manifest


def main() -> None:
    s = get_settings()
    manifest = build(
        s.kb_path, s.index_path, s.EMBEDDING_MODEL, s.CHUNK_SIZE_TOKENS, s.CHUNK_OVERLAP_TOKENS
    )
    print(
        f"Built index: {manifest['num_docs']} documents, {manifest['num_chunks']} chunks "
        f"-> {s.index_path}"
    )


if __name__ == "__main__":
    main()
