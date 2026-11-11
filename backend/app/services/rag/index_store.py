"""Vector index plus a JSON metadata sidecar (spec §10.4).

Search is *exact* cosine similarity: vectors are L2-normalised, so the inner product
equals the cosine. We use FAISS `IndexFlatIP` when it is available. If the FAISS native
library cannot be loaded (for example, Windows Application Control can block its DLL),
we fall back to the same exact search using a numpy matrix product. For a knowledge base
of a few hundred chunks both give identical results, and numpy is just as fast.

Files in INDEX_DIR:
  faiss.index    FAISS index (only written when FAISS is available)
  vectors.npy    the same vectors as a numpy array (always written; used by the fallback)
  chunks.json    chunk metadata, in the same order as the vectors
  manifest.json  embedding model, counts, build time and a hash of the KB content
"""

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger("medbridge.index")

try:  # FAISS is preferred, but optional at runtime.
    import faiss

    FAISS_AVAILABLE = True
except ImportError:  # includes "DLL load failed"
    faiss = None
    FAISS_AVAILABLE = False

INDEX_FILE = "faiss.index"
VECTORS_FILE = "vectors.npy"
CHUNKS_FILE = "chunks.json"
MANIFEST_FILE = "manifest.json"


class IndexStore:
    def __init__(self) -> None:
        self.vectors: np.ndarray | None = None  # numpy fallback
        self.faiss_index = None  # FAISS IndexFlatIP when available
        self.chunks: list[dict] = []
        self.manifest: dict = {}
        self.ready = False  # /api/ask returns 503 INDEX_NOT_READY while this is False

    @property
    def backend(self) -> str:
        return "faiss" if self.faiss_index is not None else "numpy"

    @property
    def size(self) -> int:
        return len(self.chunks)

    # ------------------------------------------------------------ save

    @staticmethod
    def save(index_dir: Path, vectors: np.ndarray, chunks: list[dict], manifest: dict) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        vectors = np.ascontiguousarray(vectors, dtype="float32")
        np.save(index_dir / VECTORS_FILE, vectors)
        if FAISS_AVAILABLE:
            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors)
            faiss.write_index(index, str(index_dir / INDEX_FILE))
        (index_dir / CHUNKS_FILE).write_text(
            json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        (index_dir / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # ------------------------------------------------------------ load & search

    def load(self, index_dir: Path, expected_model: str) -> bool:
        """Load the index from disk. Returns True if it is ready to use."""
        self.ready = False
        required = [index_dir / f for f in (VECTORS_FILE, CHUNKS_FILE, MANIFEST_FILE)]
        if not all(p.exists() for p in required):
            logger.error(
                "Knowledge base index not found in %s. Run `python -m scripts.build_index` "
                "from the backend folder.",
                index_dir,
            )
            return False

        manifest = json.loads((index_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        if manifest.get("embedding_model") != expected_model:
            # Vectors from a different model are not comparable with query vectors.
            logger.error(
                "Index was built with %s but EMBEDDING_MODEL is %s. Rebuild the index.",
                manifest.get("embedding_model"),
                expected_model,
            )
            return False

        self.chunks = json.loads((index_dir / CHUNKS_FILE).read_text(encoding="utf-8"))
        self.manifest = manifest
        self.faiss_index = None
        self.vectors = None
        if FAISS_AVAILABLE and (index_dir / INDEX_FILE).exists():
            self.faiss_index = faiss.read_index(str(index_dir / INDEX_FILE))
            count = self.faiss_index.ntotal
        else:
            self.vectors = np.load(index_dir / VECTORS_FILE)
            count = len(self.vectors)

        if count != len(self.chunks):
            logger.error("Index and chunks.json are out of sync. Rebuild the index.")
            return False
        self.ready = True
        logger.info(
            "Knowledge base index loaded (%s): %d chunks from %d documents",
            self.backend,
            len(self.chunks),
            manifest.get("num_docs", 0),
        )
        return True

    def search(self, query_vector: np.ndarray, k: int) -> list[tuple[dict, float]]:
        """Return the k most similar chunks as (chunk metadata, cosine score), best first."""
        if not self.ready or not self.chunks:
            return []
        k = min(k, self.size)
        query = np.asarray(query_vector, dtype="float32").reshape(1, -1)

        if self.faiss_index is not None:
            scores, ids = self.faiss_index.search(query, k)
            pairs = zip(ids[0], scores[0], strict=True)
        else:
            sims = self.vectors @ query[0]  # cosine similarity with every chunk
            top = np.argsort(-sims)[:k]
            pairs = zip(top, sims[top], strict=True)
        return [(self.chunks[int(i)], float(s)) for i, s in pairs if i >= 0]


# One shared store for the running app, loaded at startup (see main.py lifespan).
store = IndexStore()
