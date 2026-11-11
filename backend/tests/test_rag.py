"""RAG tests: chunking, retrieval on a tiny index, no-answer path, citation mapping (spec §14.2).

Uses the real embedding model (downloaded once, ~90 MB) on a 3-document index built
in a temporary folder. The LLM is always mocked.
"""

import shutil
import time
from pathlib import Path

import pytest

from app.config import get_settings
from app.schemas import AskRequest, ReportContext, SlimTest
from app.services.rag import answerer
from app.services.rag.chunker import chunk_file, parse_frontmatter, split_long_text
from app.services.rag.index_store import IndexStore
from app.services.rag.retriever import ScoredChunk, expand_query, retrieve
from scripts.build_index import build

KB = Path(__file__).resolve().parent.parent / "knowledge_base"
FIXTURE_DOCS = ["cbc/haemoglobin.md", "lipid/ldl-cholesterol.md", "metabolic/hba1c.md"]


@pytest.fixture(scope="module")
def tiny_store(tmp_path_factory) -> IndexStore:
    """Build an index from 3 KB documents in a temp dir and load it."""
    root = tmp_path_factory.mktemp("rag")
    kb_dir, index_dir = root / "kb", root / "index"
    for rel in FIXTURE_DOCS:
        (kb_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(KB / rel, kb_dir / rel)
    s = get_settings()
    build(kb_dir, index_dir, s.EMBEDDING_MODEL, s.CHUNK_SIZE_TOKENS, s.CHUNK_OVERLAP_TOKENS)
    store = IndexStore()
    assert store.load(index_dir, s.EMBEDDING_MODEL)
    return store


# ------------------------------------------------------------------ chunking


def test_frontmatter_and_sections() -> None:
    meta, body = parse_frontmatter((KB / "cbc/haemoglobin.md").read_text(encoding="utf-8"))
    assert meta["title"] == "Haemoglobin (Hb)"
    assert "hb" in meta["aliases"]
    assert meta["source_url"].startswith("https://")
    chunks = chunk_file(KB / "cbc/haemoglobin.md", 350, 50)
    assert chunks[0].section == "What it measures"
    assert "Aliases:" in chunks[0].embed_text and "Aliases:" not in chunks[0].text


def test_long_text_is_split_with_overlap() -> None:
    text = "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(6))
    pieces = split_long_text(text, max_chars=400, overlap_chars=50)
    assert len(pieces) > 1
    assert all(len(p) <= 400 + 50 + 2 for p in pieces)


def test_knowledge_base_has_enough_documents() -> None:
    docs = list(KB.rglob("*.md"))
    assert len(docs) >= 25
    for doc in docs:
        meta, _ = parse_frontmatter(doc.read_text(encoding="utf-8"))
        assert meta.get("source_name") and meta.get("source_url"), doc.name


# ------------------------------------------------------------------ retrieval


def test_hb_retrieves_haemoglobin_first(tiny_store) -> None:
    hits = retrieve("what is hb", store=tiny_store)
    assert hits and hits[0].chunk["doc_slug"] == "haemoglobin"
    # At most 2 chunks from any one document.
    slugs = [h.chunk["doc_slug"] for h in hits]
    assert max(slugs.count(s) for s in set(slugs)) <= 2


def test_off_topic_query_has_no_hits(tiny_store) -> None:
    assert retrieve("who won the cricket match yesterday", store=tiny_store) == []


def test_query_expansion_uses_abnormal_tests() -> None:
    ctx = ReportContext(
        tests=[
            SlimTest(name="Haemoglobin", value=10.8, status="low"),
            SlimTest(name="Platelets", value=245000, status="normal"),
        ]
    )
    assert expand_query("why is my value low?", ctx) == "why is my value low? Haemoglobin"
    assert expand_query("what is ldl?", ctx) == "what is ldl?"  # not personal → unchanged


# ------------------------------------------------------------------ answering


async def test_no_hits_returns_fixed_answer_without_llm(fake_llm) -> None:
    res = await answerer.answer(AskRequest(question="cricket?"), [], started=time.perf_counter())
    assert res.grounded is False and res.sources == []
    assert res.answer == answerer.NO_ANSWER_TEXT
    assert len(res.follow_up_suggestions) == 3
    assert fake_llm.calls == []  # the LLM was never called


def _hit(slug: str, title: str, score: float = 0.6) -> ScoredChunk:
    return ScoredChunk(
        chunk={
            "doc_slug": slug,
            "title": title,
            "section": "What it measures",
            "source_name": "MedlinePlus",
            "source_url": "https://medlineplus.gov/x",
            "text": f"{title} text.",
        },
        score=score,
    )


async def test_only_cited_sources_are_returned(fake_llm) -> None:
    hits = [_hit("haemoglobin", "Haemoglobin"), _hit("ldl", "LDL"), _hit("hba1c", "HbA1c")]
    fake_llm.text_responses = [
        "LDL is often called bad cholesterol [2]. Your LDL is high [Report].\n"
        "FOLLOW_UPS: What is HDL? | How is LDL measured?"
    ]
    req = AskRequest(
        question="What is LDL?",
        report_context=ReportContext(tests=[SlimTest(name="LDL", value=162, status="high")]),
    )
    res = await answerer.answer(req, hits, started=time.perf_counter())

    assert [s.id for s in res.sources] == [2] and res.sources[0].title == "LDL"
    assert res.grounded is True and res.used_report_context is True
    assert res.follow_up_suggestions == ["What is HDL?", "How is LDL measured?"]
    assert "FOLLOW_UPS" not in res.answer
    prompt = fake_llm.calls[0]["messages"][0]["content"]
    assert "[2] (Title: LDL" in prompt and "LDL: 162 (lab range: not given)" in prompt


async def test_uncited_grounded_answer_returns_all_sources(fake_llm) -> None:
    hits = [_hit("haemoglobin", "Haemoglobin"), _hit("ldl", "LDL")]
    fake_llm.text_responses = ["Haemoglobin carries oxygen."]
    res = await answerer.answer(AskRequest(question="hb?"), hits, started=time.perf_counter())
    assert [s.id for s in res.sources] == [1, 2]


async def test_model_saying_not_found_is_ungrounded(fake_llm) -> None:
    fake_llm.text_responses = ["I couldn't find this in MedBridge's knowledge base."]
    res = await answerer.answer(
        AskRequest(question="hb?"), [_hit("haemoglobin", "Hb")], started=time.perf_counter()
    )
    assert res.grounded is False and res.sources == []


async def test_fullwidth_markers_are_normalised(fake_llm) -> None:
    fake_llm.text_responses = ["Your Hb is low【Report】 and carries oxygen【1】."]
    req = AskRequest(
        question="Why is my hb low?",
        report_context=ReportContext(tests=[SlimTest(name="Hb", value=10.8, status="low")]),
    )
    res = await answerer.answer(req, [_hit("haemoglobin", "Hb")], started=time.perf_counter())
    assert "[Report]" in res.answer and "[1]" in res.answer
    assert res.used_report_context is True and [s.id for s in res.sources] == [1]
