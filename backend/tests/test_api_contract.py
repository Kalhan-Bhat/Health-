"""End-to-end API tests with a mocked LLM (spec §14.2).

Checks that responses validate against the Pydantic models and that errors use the
uniform envelope.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AnalyzeReportResponse, AskResponse
from app.services.rag import index_store as index_module
from app.services.rag import retriever
from tests.conftest import CBC_EXPLANATION, CBC_EXTRACTION

FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(app)  # no `with` block, so the lifespan (index loading) is skipped


def _upload(name: str, extra: dict | None = None):
    return client.post(
        "/api/analyze-report",
        files={"file": (name, (FIXTURES / name).read_bytes(), "application/pdf")},
        data=extra or {},
    )


def _assert_envelope(res, status: int, code: str) -> None:
    assert res.status_code == status, res.text
    err = res.json()["error"]
    assert err["code"] == code and err["message"] and isinstance(err["details"], dict)


# ------------------------------------------------------------------ analyze


def test_analyze_happy_path(fake_llm) -> None:
    fake_llm.json_responses = [CBC_EXTRACTION, CBC_EXPLANATION]
    res = _upload("sample_cbc_low_hb.pdf", {"reading_level": "detailed"})
    assert res.status_code == 200, res.text
    body = AnalyzeReportResponse.model_validate(res.json())
    hb = next(t for t in body.tests if t.name == "Haemoglobin")
    assert hb.status == "low"
    assert len(body.doctor_questions) >= 4 and body.disclaimer
    assert body.meta.pages == 1


def test_analyze_not_a_report(fake_llm) -> None:
    fake_llm.json_responses = [{"report_type": "Essay", "tests": []}]
    _assert_envelope(_upload("not_a_report.pdf"), 422, "NOT_A_LAB_REPORT")


def test_analyze_bad_reading_level(fake_llm) -> None:
    _assert_envelope(
        _upload("sample_cbc_low_hb.pdf", {"reading_level": "expert"}), 422, "VALIDATION_ERROR"
    )


# ------------------------------------------------------------------ ask


@pytest.fixture
def ready_index(monkeypatch: pytest.MonkeyPatch):
    """Pretend the index is loaded and control what retrieval returns."""
    monkeypatch.setattr(index_module.store, "ready", True)
    hits: list = []
    monkeypatch.setattr(retriever, "retrieve", lambda q, ctx=None: hits)
    return hits


def test_ask_emergency_skips_llm(fake_llm) -> None:
    res = client.post("/api/ask", json={"question": "I have chest pain right now"})
    body = AskResponse.model_validate(res.json())
    assert "emergency" in body.answer.lower() and body.sources == []
    assert fake_llm.calls == []


def test_ask_index_not_ready(fake_llm, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(index_module.store, "ready", False)
    _assert_envelope(
        client.post("/api/ask", json={"question": "What is LDL?"}), 503, "INDEX_NOT_READY"
    )


def test_ask_no_hits(fake_llm, ready_index) -> None:
    res = client.post("/api/ask", json={"question": "who won the cricket match"})
    body = AskResponse.model_validate(res.json())
    assert body.grounded is False and body.sources == [] and fake_llm.calls == []


def test_ask_grounded_answer(fake_llm, ready_index) -> None:
    ready_index.append(
        retriever.ScoredChunk(
            chunk={
                "doc_slug": "ldl-cholesterol",
                "title": "LDL Cholesterol",
                "section": "What it measures",
                "source_name": "MedlinePlus",
                "source_url": "https://medlineplus.gov/ldl",
                "text": "LDL carries cholesterol.",
            },
            score=0.7,
        )
    )
    fake_llm.text_responses = ["LDL is bad cholesterol [1].\nFOLLOW_UPS: What is HDL? | Why fast?"]
    res = client.post("/api/ask", json={"question": "What is LDL?"})
    body = AskResponse.model_validate(res.json())
    assert body.grounded and body.sources[0].source_url == "https://medlineplus.gov/ldl"


@pytest.mark.parametrize(
    "payload, status, code",
    [
        ({"question": "  a  "}, 400, "INVALID_QUESTION"),
        ({"question": "hi"}, 422, "VALIDATION_ERROR"),
        ({"question": "x" * 501}, 422, "VALIDATION_ERROR"),
        ({}, 422, "VALIDATION_ERROR"),
    ],
)
def test_ask_invalid_questions(fake_llm, payload, status, code) -> None:
    _assert_envelope(client.post("/api/ask", json=payload), status, code)
