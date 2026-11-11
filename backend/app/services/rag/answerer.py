"""Build the grounded prompt, call Groq, and map citations to sources (spec §9.3, §10.6)."""

import re
import time

from app.prompts.rag_answer import (
    CHUNK_TEMPLATE,
    RAG_SYSTEM,
    RAG_USER_TEMPLATE,
    REPORT_LINE_TEMPLATE,
)
from app.safety import guardrails
from app.safety.disclaimers import DISCLAIMER, EMERGENCY_MESSAGE
from app.schemas import AskMeta, AskRequest, AskResponse, ReportContext, Source
from app.services import llm_client
from app.services.rag.retriever import ScoredChunk

NO_ANSWER_TEXT = (
    "I couldn't find information about that in MedBridge's knowledge base. MedBridge covers "
    "common lab tests such as blood counts, cholesterol, blood sugar, kidney, liver and thyroid "
    "tests. For other questions, please ask your doctor or pharmacist."
)

STATIC_FOLLOW_UPS = [
    "What does a complete blood count (CBC) measure?",
    "What is the difference between LDL and HDL cholesterol?",
    "What does a reference range mean?",
]

_CITATION_RE = re.compile(r"\[(\d+)\]")
_FOLLOW_UPS_RE = re.compile(r"^\s*\**FOLLOW[_ ]UPS\**\s*:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
_NOT_FOUND_PHRASE = "couldn't find this in medbridge"
# Some models write markers with full-width brackets, e.g. 【1】 or 【Report】.
_FULLWIDTH_MARKER_RE = re.compile(r"【\s*([^】]{1,20}?)\s*】")
SNIPPET_CHARS = 220


async def answer(req: AskRequest, hits: list[ScoredChunk], *, started: float) -> AskResponse:
    """Answer a question from retrieved chunks. With no hits, return the fixed no-answer."""
    llm = llm_client.get_llm_client()
    used_report = bool(req.report_context and req.report_context.tests)

    # No chunk passed the similarity threshold → do NOT call the LLM (no hallucination).
    if not hits:
        return AskResponse(
            answer=NO_ANSWER_TEXT,
            grounded=False,
            sources=[],
            used_report_context=False,
            follow_up_suggestions=STATIC_FOLLOW_UPS,
            disclaimer=DISCLAIMER,
            meta=AskMeta(model=llm.model, retrieved=0, processing_ms=_ms(started)),
        )

    user_prompt = RAG_USER_TEMPLATE.format(
        numbered_chunks=build_numbered_chunks(hits),
        report_block=build_report_block(req.report_context) if used_report else "",
        history_block=build_history_block(req),
        question=req.question.strip(),
    )
    raw = await llm.chat_text(RAG_SYSTEM, [{"role": "user", "content": user_prompt}])

    text, follow_ups = split_follow_ups(normalize_markers(raw))
    sources = select_sources(text, hits)
    grounded = bool(sources) and _NOT_FOUND_PHRASE not in text.lower()
    if not grounded:
        sources = []

    return AskResponse(
        answer=guardrails.post_check_answer(text),
        grounded=grounded,
        sources=sources,
        used_report_context=used_report and "[Report]" in text,
        follow_up_suggestions=follow_ups,
        disclaimer=DISCLAIMER,
        meta=AskMeta(model=llm.model, retrieved=len(hits), processing_ms=_ms(started)),
    )


def emergency_response(*, started: float) -> AskResponse:
    """Fixed emergency message, returned without calling the LLM (spec §12)."""
    return AskResponse(
        answer=EMERGENCY_MESSAGE,
        grounded=False,
        sources=[],
        used_report_context=False,
        follow_up_suggestions=[],
        disclaimer=DISCLAIMER,
        meta=AskMeta(
            model=llm_client.get_llm_client().model, retrieved=0, processing_ms=_ms(started)
        ),
    )


# ------------------------------------------------------------------ prompt pieces


def build_numbered_chunks(hits: list[ScoredChunk]) -> str:
    return "\n\n".join(
        CHUNK_TEMPLATE.format(
            n=i,
            title=h.chunk["title"],
            section=h.chunk["section"],
            source_name=h.chunk["source_name"],
            text=h.chunk["text"],
        )
        for i, h in enumerate(hits, start=1)
    )


def build_report_block(ctx: ReportContext | None) -> str:
    if not ctx or not ctx.tests:
        return ""
    lines = [f"User's report data ({ctx.report_type or 'lab report'}):"]
    for t in ctx.tests:
        value = "not given" if t.value is None else f"{t.value:g} {t.unit or ''}".strip()
        lines.append(
            REPORT_LINE_TEMPLATE.format(
                name=t.name,
                value=value,
                range=t.reference_range_raw or "not given",
                status=t.status,
            )
        )
    return "\n".join(lines)


def build_history_block(req: AskRequest) -> str:
    if not req.history:
        return "(none)"
    return "\n".join(
        f"{'User' if turn.role == 'user' else 'Assistant'}: {turn.content}"
        for turn in req.history[-6:]
    )


# ------------------------------------------------------------------ reply parsing


def normalize_markers(raw: str) -> str:
    """Turn 【1】 / 【Report】 into [1] / [Report] so citations are recognised."""
    return _FULLWIDTH_MARKER_RE.sub(r"[\1]", raw)


def split_follow_ups(raw: str) -> tuple[str, list[str]]:
    """Separate the trailing 'FOLLOW_UPS: a | b' line from the answer text."""
    match = _FOLLOW_UPS_RE.search(raw)
    if not match:
        return raw.strip(), []
    follow_ups = [q.strip(" -*\t") for q in match.group(1).split("|") if q.strip(" -*\t")]
    text = raw[: match.start()].strip()
    return text, follow_ups[:3]


def select_sources(text: str, hits: list[ScoredChunk]) -> list[Source]:
    """Return only the sources the answer actually cited; if none were cited, all of them."""
    cited = {int(n) for n in _CITATION_RE.findall(text) if 1 <= int(n) <= len(hits)}
    numbers = sorted(cited) if cited else range(1, len(hits) + 1)
    return [to_source(n, hits[n - 1]) for n in numbers]


def to_source(n: int, hit: ScoredChunk) -> Source:
    text = " ".join(hit.chunk["text"].split())
    snippet = text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "…"
    return Source(
        id=n,  # matches the [n] marker in the answer text
        title=hit.chunk["title"],
        section=hit.chunk.get("section"),
        source_name=hit.chunk["source_name"],
        source_url=hit.chunk.get("source_url"),
        snippet=snippet,
        score=round(hit.score, 3),
    )


def _ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
