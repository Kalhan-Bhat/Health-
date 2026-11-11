"""Live checks against the real Groq API (spec §15, Phase 2 and Phase 4 acceptance).

Skipped by default. Run with a real key in backend/.env:
    pytest -m live
"""

import time
from pathlib import Path

import pytest

from app.config import get_settings
from app.services.pdf_extractor import validate_and_extract
from app.services.report_analyzer import analyze_report

pytestmark = pytest.mark.live
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _require_key() -> None:
    if not get_settings().has_api_key:
        pytest.skip("GROQ_API_KEY is not set in backend/.env")


async def test_live_cbc_analysis() -> None:
    data = (FIXTURES / "sample_cbc_low_hb.pdf").read_bytes()
    started = time.perf_counter()
    result = await analyze_report(
        validate_and_extract(data, "sample_cbc_low_hb.pdf", "application/pdf"), "simple"
    )
    elapsed = time.perf_counter() - started

    hb = next(t for t in result.tests if "haemoglobin" in t.name.lower())
    assert hb.status == "low"
    assert len(result.doctor_questions) >= 4
    assert result.disclaimer
    assert elapsed < 15, f"analysis took {elapsed:.1f}s"
