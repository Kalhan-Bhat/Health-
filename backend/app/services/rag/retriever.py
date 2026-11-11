"""Question → relevant knowledge-base chunks (spec §10.5)."""

import re
from dataclasses import dataclass

from app.config import get_settings
from app.schemas import ReportContext
from app.services.rag.embedder import get_embedder
from app.services.rag.index_store import IndexStore
from app.services.rag.index_store import store as default_store

MAX_CHUNKS_PER_DOC = 2
# How many candidates to fetch before filtering, so de-duplication still leaves enough.
CANDIDATE_MULTIPLIER = 3

_PERSONAL_REFERENCE_RE = re.compile(r"\b(my|mine|this|it|these|that)\b", re.IGNORECASE)


@dataclass
class ScoredChunk:
    chunk: dict
    score: float


def expand_query(question: str, report_context: ReportContext | None) -> str:
    """If the user asks about "my" result, add the names of their abnormal tests.

    "Why is my value low?" + report with low Haemoglobin → "Why is my value low? Haemoglobin".
    This helps the search find the right document for vague, personal questions.
    """
    if not report_context or not report_context.tests:
        return question
    if not _PERSONAL_REFERENCE_RE.search(question):
        return question
    abnormal = [t.name for t in report_context.tests if t.status in ("low", "high", "borderline")]
    if not abnormal:
        return question
    return f"{question} {' '.join(abnormal[:5])}"


def retrieve(
    question: str,
    report_context: ReportContext | None = None,
    *,
    store: IndexStore | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[ScoredChunk]:
    """Embed the question, search FAISS, drop weak hits and keep ≤ 2 chunks per document."""
    settings = get_settings()
    store = store or default_store
    top_k = top_k or settings.RAG_TOP_K
    min_score = settings.RAG_MIN_SCORE if min_score is None else min_score

    query = expand_query(question, report_context)
    vector = get_embedder(settings.EMBEDDING_MODEL).embed([query])[0]

    results: list[ScoredChunk] = []
    per_doc: dict[str, int] = {}
    for chunk, score in store.search(vector, top_k * CANDIDATE_MULTIPLIER):
        if score < min_score:
            break  # results are sorted best-first, so the rest are weaker
        slug = chunk["doc_slug"]
        if per_doc.get(slug, 0) >= MAX_CHUNKS_PER_DOC:
            continue
        per_doc[slug] = per_doc.get(slug, 0) + 1
        results.append(ScoredChunk(chunk=chunk, score=score))
        if len(results) >= top_k:
            break
    return results
