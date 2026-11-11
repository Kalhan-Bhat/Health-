"""Orchestrates Feature F1: report text → validated tests → plain-language explanation.

Flow (spec §4, §8.5):
  1. LLM call #1 extracts raw strings (name, value, unit, range, flag) as JSON.
  2. Python validates every row, parses numbers/ranges and computes the status.
     Bad rows never crash the request; they go to `unparsed_lines`.
  3. LLM call #2 writes explanations, seeing ONLY the validated tests (never the raw PDF).
  4. Python merges everything, counts statuses and adds red flags + the disclaimer.
"""

import json
import logging
import time
import uuid
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.errors import AppError
from app.prompts.explanation import build_explanation_system, build_explanation_user
from app.prompts.extraction import EXTRACTION_SYSTEM, build_extraction_user
from app.safety import guardrails
from app.safety.disclaimers import DISCLAIMER
from app.schemas import (
    AnalyzeMeta,
    AnalyzeReportResponse,
    LabTest,
    PatientContext,
    ReportSummary,
    StatusCounts,
    TestExplanation,
)
from app.services import llm_client
from app.services.pdf_extractor import ExtractedPDF
from app.services.range_parser import compute_status, parse_number, parse_range

logger = logging.getLogger("medbridge.analyzer")

MAX_TESTS = 60
MAX_UNPARSED_LINES = 15

# --------------------------------------------------------------------------
# Internal models for what the LLM sends back. They are lenient on purpose:
# numbers are turned into strings, and anything missing becomes None.
# --------------------------------------------------------------------------


def _to_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


class RawTest(BaseModel):
    name: str
    category: str | None = None
    value_raw: str
    unit: str | None = None
    reference_range_raw: str | None = None
    lab_flag: str | None = None

    @field_validator("name", "value_raw", mode="before")
    @classmethod
    def _required_text(cls, v: Any) -> str:
        s = _to_str(v)
        if s is None:
            raise ValueError("missing")
        return s

    @field_validator("category", "unit", "reference_range_raw", "lab_flag", mode="before")
    @classmethod
    def _optional_text(cls, v: Any) -> str | None:
        return _to_str(v)


class RawExplanation(BaseModel):
    id: str
    what_it_measures: str | None = None
    what_your_result_means: str | None = None
    common_reasons: str | None = None
    range_note: str | None = None


class RawExplanationResponse(BaseModel):
    """Shape of LLM call #2. Also used as the JSON schema when GROQ_USE_JSON_SCHEMA=true."""

    overview: str = ""
    key_findings: list[str] = Field(default_factory=list)
    explanations: list[RawExplanation] = Field(default_factory=list)
    doctor_questions: list[str] = Field(default_factory=list)


# Used to top up the list if the LLM returns fewer than 4 questions.
GENERIC_DOCTOR_QUESTIONS = [
    "Which of these results are most important for me to understand?",
    "Do any of these results need follow-up tests, and if so, which ones?",
    "Should any of these tests be repeated, and when?",
    "Could any of my current medicines or habits affect these results?",
    "Is there anything in this report you would like to keep an eye on over time?",
]
MIN_DOCTOR_QUESTIONS = 4


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------


async def analyze_report(
    extracted: ExtractedPDF, reading_level: str, *, started: float | None = None
) -> AnalyzeReportResponse:
    started = started if started is not None else time.perf_counter()
    llm = llm_client.get_llm_client()

    # ---- 1) Extraction (LLM call #1) -------------------------------------
    safe_text = guardrails.sanitize_report_text(extracted.text)
    raw = await llm.chat_json(EXTRACTION_SYSTEM, build_extraction_user(safe_text))

    # ---- 2) Deterministic validation + status ----------------------------
    tests, unparsed = normalize_tests(raw.get("tests"))
    if not tests:
        raise AppError(
            "NOT_A_LAB_REPORT",
            422,
            "We couldn't find lab test results in this file. "
            "Please upload a laboratory report PDF.",
        )
    tests = dedupe_by_name(tests)[:MAX_TESTS]
    for i, test in enumerate(tests, start=1):
        test.id = f"t{i}"

    unparsed = _clean_lines(raw.get("unparsed_lines")) + unparsed
    report_type = _to_str(raw.get("report_type")) or "Lab Report"
    patient_context = _parse_patient_context(raw.get("patient_context"))

    # ---- 3) Explanation (LLM call #2) — only validated data goes in ---------
    expl = await _explain(tests, report_type, patient_context, reading_level, llm)

    # ---- 4) Merge ----------------------------------------------------------
    attach_explanations(tests, expl.explanations)
    counts = compute_counts(tests)
    overview = expl.overview.strip() or _fallback_overview(report_type, counts)
    key_findings = [k for k in expl.key_findings if k.strip()][:5] or _fallback_findings(tests)
    doctor_questions = _top_up_questions(expl.doctor_questions)

    return AnalyzeReportResponse(
        report_id=str(uuid.uuid4()),  # session-only id, not stored anywhere
        report_type=report_type,
        patient_context=patient_context,
        summary=ReportSummary(overview=overview, key_findings=key_findings, counts=counts),
        tests=tests,
        doctor_questions=doctor_questions,
        red_flags=guardrails.detect_red_flags(tests, extracted.text),
        unparsed_lines=unparsed[:MAX_UNPARSED_LINES],
        disclaimer=DISCLAIMER,
        meta=AnalyzeMeta(
            pages=extracted.pages,
            extraction_method=extracted.method,
            model=llm.model,
            processing_ms=int((time.perf_counter() - started) * 1000),
        ),
    )


# --------------------------------------------------------------------------
# Step 2 helpers (pure functions — unit tested)
# --------------------------------------------------------------------------


def normalize_tests(raw_tests: Any) -> tuple[list[LabTest], list[str]]:
    """Validate raw LLM rows and compute each status. Never raises on a bad row.

    Returns (valid tests, unparsed line strings).
    """
    tests: list[LabTest] = []
    unparsed: list[str] = []
    if not isinstance(raw_tests, list):
        return tests, unparsed

    for row in raw_tests:
        if not isinstance(row, dict):
            if _to_str(row):
                unparsed.append(str(row)[:200])
            continue
        try:
            rt = RawTest.model_validate(row)
        except ValidationError:
            # Keep whatever text the row had so the user can still see it.
            text = " ".join(str(v) for v in row.values() if v not in (None, ""))
            if text:
                unparsed.append(text[:200])
            continue
        tests.append(build_lab_test(rt))
    return tests, unparsed


def build_lab_test(rt: RawTest, test_id: str = "") -> LabTest:
    """Parse numbers and the range, then decide the status in code (not by the LLM)."""
    value = parse_number(rt.value_raw)
    ref_low, ref_high = parse_range(rt.reference_range_raw)
    status, source = compute_status(value, ref_low, ref_high, rt.lab_flag)

    # Qualitative result that matches the expected result, e.g. "Negative" vs "Negative".
    if (
        status == "unknown"
        and value is None
        and rt.reference_range_raw
        and rt.value_raw.strip().lower() == rt.reference_range_raw.strip().lower()
    ):
        status, source = "normal", "computed"

    return LabTest(
        id=test_id,
        name=rt.name,
        category=rt.category,
        value_raw=rt.value_raw,
        value=value,
        unit=rt.unit,
        reference_range_raw=rt.reference_range_raw,
        ref_low=ref_low,
        ref_high=ref_high,
        lab_flag=rt.lab_flag,
        status=status,
        status_source=source,
    )


def dedupe_by_name(tests: list[LabTest]) -> list[LabTest]:
    """Drop repeated rows (same test name), keeping the first one."""
    seen: set[str] = set()
    unique: list[LabTest] = []
    for t in tests:
        key = " ".join(t.name.lower().split())
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


def compute_counts(tests: list[LabTest]) -> StatusCounts:
    """Counts are computed in Python, never by the LLM."""
    by_status = {s: 0 for s in ("normal", "low", "high", "borderline", "unknown")}
    for t in tests:
        by_status[t.status] += 1
    return StatusCounts(total=len(tests), **by_status)


# --------------------------------------------------------------------------
# Step 3 / 4 helpers
# --------------------------------------------------------------------------


async def _explain(
    tests: list[LabTest],
    report_type: str,
    patient_context: PatientContext,
    reading_level: str,
    llm: "llm_client.LLMClient",
) -> RawExplanationResponse:
    tests_for_prompt = [
        t.model_dump(
            include={
                "id",
                "name",
                "category",
                "value",
                "unit",
                "reference_range_raw",
                "ref_low",
                "ref_high",
                "status",
            }
        )
        for t in tests
    ]
    user = build_explanation_user(
        report_type=report_type,
        patient_context_json=json.dumps(patient_context.model_dump(), ensure_ascii=False),
        tests_json=json.dumps(tests_for_prompt, ensure_ascii=False, indent=1),
        num_tests=len(tests),
    )
    # Big panels need more room for the JSON reply.
    max_tokens = 4096 if len(tests) > 10 else None
    raw = await llm.chat_json(
        build_explanation_system(reading_level),
        user,
        max_tokens=max_tokens,
        json_schema=RawExplanationResponse.model_json_schema(),
        schema_name="report_explanation",
    )
    try:
        return RawExplanationResponse.model_validate(_lenient_explanation(raw))
    except ValidationError:
        logger.warning("Explanation JSON did not match the expected shape; using fallbacks")
        return RawExplanationResponse()


def _lenient_explanation(raw: dict) -> dict:
    """Keep only well-formed parts of the explanation reply."""

    def str_list(v: Any) -> list[str]:
        return [str(x).strip() for x in v if _to_str(x)] if isinstance(v, list) else []

    explanations = []
    for e in raw.get("explanations") or []:
        if isinstance(e, dict) and _to_str(e.get("id")):
            explanations.append(
                {k: _to_str(e.get(k)) for k in RawExplanation.model_fields} | {"id": str(e["id"])}
            )
    return {
        "overview": _to_str(raw.get("overview")) or "",
        "key_findings": str_list(raw.get("key_findings")),
        "explanations": explanations,
        "doctor_questions": str_list(raw.get("doctor_questions")),
    }


def attach_explanations(tests: list[LabTest], explanations: list[RawExplanation]) -> None:
    """Match explanations to tests by id. Missing ones get a safe, generic text."""
    by_id = {e.id: e for e in explanations}
    for t in tests:
        e = by_id.get(t.id)
        common = e.common_reasons if e else None
        if t.status == "normal":
            common = None  # only explain reasons for out-of-range results
        elif not common and t.status in ("low", "high", "borderline"):
            common = (
                "Results outside the reference range can have many causes, and some are "
                "temporary. Only your doctor can tell what this result means for you."
            )
        t.explanation = TestExplanation(
            what_it_measures=(e.what_it_measures if e and e.what_it_measures else None)
            or f"{t.name} is one of the measurements in your {t.category or 'report'}.",
            what_your_result_means=(
                e.what_your_result_means if e and e.what_your_result_means else None
            )
            or describe_result(t),
            common_reasons=common,
            range_note=(e.range_note if e else None)
            or "Reference ranges are set by each lab and can differ between labs, ages and sexes.",
        )


_STATUS_WORDS = {
    "low": "below the lab's reference range",
    "high": "above the lab's reference range",
    "normal": "within the lab's reference range",
    "borderline": "marked as borderline by the lab",
    "unknown": "not something MedBridge could compare automatically — please check your report",
}


def describe_result(t: LabTest) -> str:
    """A deterministic one-sentence description, used if the LLM skipped a test."""
    value = f"{t.value_raw} {t.unit}".strip() if t.unit else t.value_raw
    rng = f" (lab range: {t.reference_range_raw})" if t.reference_range_raw else ""
    return f"Your result of {value}{rng} is {_STATUS_WORDS[t.status]}."


def _fallback_overview(report_type: str, counts: StatusCounts) -> str:
    out = counts.low + counts.high + counts.borderline
    return (
        f"This is a {report_type} with {counts.total} results. "
        f"{counts.normal} are within the lab's reference ranges and {out} are outside them "
        "or marked by the lab. Your doctor can explain what these results mean for you."
    )


def _fallback_findings(tests: list[LabTest]) -> list[str]:
    findings = [f"{t.name} is {_STATUS_WORDS[t.status]}." for t in tests if t.status != "normal"]
    return findings[:5] or ["All results are within the lab's reference ranges."]


def _top_up_questions(questions: list[str]) -> list[str]:
    qs = [q.strip() for q in questions if q.strip()][:8]
    for generic in GENERIC_DOCTOR_QUESTIONS:
        if len(qs) >= MIN_DOCTOR_QUESTIONS:
            break
        if generic not in qs:
            qs.append(generic)
    return qs


def _parse_patient_context(raw: Any) -> PatientContext:
    if not isinstance(raw, dict):
        return PatientContext()
    return PatientContext(**{k: _to_str(raw.get(k)) for k in PatientContext.model_fields})


def _clean_lines(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(x).strip()[:200] for x in raw if _to_str(x)][:10]
