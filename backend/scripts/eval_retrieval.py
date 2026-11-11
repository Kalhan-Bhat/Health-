"""Evaluate retrieval quality on seed questions (spec §10.7).

Run from the backend/ folder (after build_index):
    python -m scripts.eval_retrieval

Prints hit@1, hit@3 and the score distribution, and writes the table to
scripts/eval_results.md for the project report. Target: hit@3 >= 0.8.
"""

import json
import statistics
import sys
from pathlib import Path

from app.config import get_settings
from app.services.rag.embedder import get_embedder
from app.services.rag.index_store import IndexStore

SCRIPTS_DIR = Path(__file__).resolve().parent


def ranked_docs(store: IndexStore, embedder, question: str, k: int = 10) -> list[tuple[str, float]]:
    """Unique document slugs in rank order, with the best score for each."""
    vector = embedder.embed([question])[0]
    seen: dict[str, float] = {}
    for chunk, score in store.search(vector, k):
        seen.setdefault(chunk["doc_slug"], score)
    return list(seen.items())


def main() -> None:
    # Windows consoles default to cp1252, which cannot print symbols such as "≥".
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = get_settings()
    store = IndexStore()
    if not store.load(s.index_path, s.EMBEDDING_MODEL):
        raise SystemExit("Index not ready. Run: python -m scripts.build_index")
    embedder = get_embedder(s.EMBEDDING_MODEL)
    data = json.loads((SCRIPTS_DIR / "eval_questions.json").read_text(encoding="utf-8"))

    rows = []
    for item in data["questions"]:
        docs = ranked_docs(store, embedder, item["question"])
        slugs = [d for d, _ in docs]
        expected = item["expected_doc_slug"]
        rank = slugs.index(expected) + 1 if expected in slugs else None
        rows.append((item["question"], expected, slugs[0], docs[0][1], rank))

    n = len(rows)
    hit1 = sum(1 for r in rows if r[4] == 1) / n
    hit3 = sum(1 for r in rows if r[4] is not None and r[4] <= 3) / n
    on_topic = [r[3] for r in rows]
    off_topic = [ranked_docs(store, embedder, q)[0][1] for q in data["off_topic_questions"]]

    lines = [
        "# Retrieval evaluation",
        "",
        f"Embedding model: `{s.EMBEDDING_MODEL}` · Documents: {store.manifest['num_docs']} · "
        f"Chunks: {store.manifest['num_chunks']} · RAG_MIN_SCORE: {s.RAG_MIN_SCORE}",
        "",
        "| # | Question | Expected document | Top result | Top score | Rank of expected |",
        "|---|---|---|---|---|---|",
    ]
    for i, (q, exp, top, score, rank) in enumerate(rows, start=1):
        lines.append(f"| {i} | {q} | {exp} | {top} | {score:.3f} | {rank or '>10'} |")
    lines += [
        "",
        f"**hit@1 = {hit1:.2f}** · **hit@3 = {hit3:.2f}** (target ≥ 0.80) · questions = {n}",
        "",
        "Score distribution (best chunk per question):",
        "",
        f"- On-topic: min {min(on_topic):.3f}, median {statistics.median(on_topic):.3f}, "
        f"max {max(on_topic):.3f}",
        f"- Off-topic: min {min(off_topic):.3f}, median {statistics.median(off_topic):.3f}, "
        f"max {max(off_topic):.3f}",
        "",
        "RAG_MIN_SCORE should sit between the highest off-topic score and the lowest "
        "on-topic score.",
    ]
    report = "\n".join(lines)
    print(report)
    (SCRIPTS_DIR / "eval_results.md").write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
