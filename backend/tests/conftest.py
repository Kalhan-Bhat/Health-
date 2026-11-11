"""Shared pytest setup.

A dummy API key is set *before* the app is imported so tests never need a real
Groq key. The `fake_llm` fixture replaces the Groq client with canned answers, so
normal test runs never call the real API (live tests are marked `@pytest.mark.live`).
"""

import copy
import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Runs before any app module is imported.

    Normal runs get a dummy key, so they never need (or use) a real one.
    `pytest -m live` keeps the real key from backend/.env instead.
    """
    os.environ.setdefault("APP_ENV", "development")
    os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")  # no rate limiting inside tests
    if config.getoption("markexpr", "").strip() != "live":
        os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")


from app.services import llm_client  # noqa: E402


class FakeLLM:
    """Stands in for LLMClient. Returns queued answers and records every call."""

    model = "fake-model"

    def __init__(self) -> None:
        self.json_responses: list[dict] = []
        self.text_responses: list[str] = []
        self.calls: list[dict] = []

    async def chat_json(self, system: str, user: str, **kwargs) -> dict:
        self.calls.append({"kind": "json", "system": system, "user": user})
        if not self.json_responses:
            raise AssertionError("FakeLLM.chat_json called but no JSON response was queued")
        return copy.deepcopy(self.json_responses.pop(0))

    async def chat_text(self, system: str, messages: list[dict], **kwargs) -> str:
        self.calls.append({"kind": "text", "system": system, "messages": messages})
        if not self.text_responses:
            raise AssertionError("FakeLLM.chat_text called but no text response was queued")
        return self.text_responses.pop(0)


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeLLM:
    fake = FakeLLM()
    monkeypatch.setattr(llm_client, "get_llm_client", lambda: fake)
    return fake


# ---------------------------------------------------------------- canned LLM output

CBC_EXTRACTION = {
    "report_type": "Complete Blood Count (CBC)",
    "patient_context": {
        "age": 34,
        "sex": "Female",
        "report_date": "2026-10-02",
        "lab_name": "Sample Diagnostics Lab",
    },
    "tests": [
        {
            "name": "Haemoglobin",
            "category": "Red Blood Cells",
            "value_raw": "10.8",
            "unit": "g/dL",
            "reference_range_raw": "12.0 - 15.5",
            "lab_flag": "L",
        },
        {
            "name": "Hematocrit (PCV)",
            "category": "Red Blood Cells",
            "value_raw": "33.1",
            "unit": "%",
            "reference_range_raw": "36 - 46",
            "lab_flag": "L",
        },
        {
            "name": "MCV",
            "category": "Red Blood Cells",
            "value_raw": "84.9",
            "unit": "fL",
            "reference_range_raw": "80 - 100",
            "lab_flag": None,
        },
        {
            "name": "Total WBC Count",
            "category": "White Blood Cells",
            "value_raw": "7,200",
            "unit": "/µL",
            "reference_range_raw": "4,000 - 11,000",
            "lab_flag": None,
        },
        {
            "name": "Platelet Count",
            "category": "Platelets",
            "value_raw": "2,45,000",
            "unit": "/µL",
            "reference_range_raw": "1,50,000 - 4,10,000",
            "lab_flag": None,
        },
    ],
    "unparsed_lines": ["Peripheral smear: Normocytic normochromic"],
}

CBC_EXPLANATION = {
    "overview": "This is a Complete Blood Count. Haemoglobin and hematocrit are below range.",
    "key_findings": ["Haemoglobin is below the lab's reference range."],
    "explanations": [
        {
            "id": "t1",
            "what_it_measures": "Haemoglobin carries oxygen.",
            "what_your_result_means": "10.8 g/dL is below 12.0–15.5 g/dL.",
            "common_reasons": "Many causes, such as low iron. Your doctor can tell.",
            "range_note": None,
        },
        {
            "id": "t3",
            "what_it_measures": "MCV is the average size of red cells.",
            "what_your_result_means": "84.9 fL is within range.",
            "common_reasons": "should be dropped for normal results",
            "range_note": None,
        },
    ],
    "doctor_questions": [
        "What could be causing my low haemoglobin?",
        "Do I need iron studies?",
        "Should this test be repeated?",
        "Is there anything I should watch for?",
    ],
}
