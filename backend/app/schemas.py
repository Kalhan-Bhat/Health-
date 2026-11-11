"""Pydantic request/response models.

These are implemented exactly as given in spec §7.3. The field names are the
contract with the frontend, so do not rename them.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["low", "normal", "high", "borderline", "unknown"]


class PatientContext(BaseModel):
    age: Optional[str] = None
    sex: Optional[str] = None
    report_date: Optional[str] = None
    lab_name: Optional[str] = None


class TestExplanation(BaseModel):
    __test__ = False  # tell pytest this is not a test class (its name starts with "Test")

    what_it_measures: str
    what_your_result_means: str
    common_reasons: Optional[str] = None
    range_note: Optional[str] = None


class LabTest(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    value_raw: str
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range_raw: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    lab_flag: Optional[str] = None
    status: Status = "unknown"
    status_source: Literal["computed", "lab_flag", "none"] = "none"
    explanation: Optional[TestExplanation] = None


class StatusCounts(BaseModel):
    total: int
    normal: int
    low: int
    high: int
    unknown: int
    borderline: int = 0


class ReportSummary(BaseModel):
    overview: str
    key_findings: list[str] = Field(default_factory=list)
    counts: StatusCounts


class RedFlag(BaseModel):
    test_id: Optional[str] = None
    message: str


class AnalyzeMeta(BaseModel):
    pages: int
    extraction_method: str
    model: str
    processing_ms: int


class AnalyzeReportResponse(BaseModel):
    report_id: str
    report_type: str
    patient_context: PatientContext
    summary: ReportSummary
    tests: list[LabTest]
    doctor_questions: list[str]
    red_flags: list[RedFlag] = Field(default_factory=list)
    unparsed_lines: list[str] = Field(default_factory=list)
    disclaimer: str
    meta: AnalyzeMeta


class SlimTest(BaseModel):
    name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range_raw: Optional[str] = None
    status: Status = "unknown"


class ReportContext(BaseModel):
    report_id: Optional[str] = None
    report_type: Optional[str] = None
    tests: list[SlimTest] = Field(default_factory=list, max_length=60)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    report_context: Optional[ReportContext] = None
    history: list[ChatTurn] = Field(default_factory=list, max_length=6)


class Source(BaseModel):
    id: int
    title: str
    section: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    snippet: str
    score: float


class AskMeta(BaseModel):
    model: str
    retrieved: int
    processing_ms: int


class AskResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[Source]
    used_report_context: bool
    follow_up_suggestions: list[str] = Field(default_factory=list)
    disclaimer: str
    meta: AskMeta
