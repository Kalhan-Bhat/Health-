"""POST /api/analyze-report — Feature F1 (report explanation).

Phase 0: returns a stub response that already matches the response model.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, File, Form, UploadFile

from app.config import get_settings
from app.safety.disclaimers import DISCLAIMER
from app.schemas import (
    AnalyzeMeta,
    AnalyzeReportResponse,
    PatientContext,
    ReportSummary,
    StatusCounts,
)

router = APIRouter()


@router.post("/analyze-report", response_model=AnalyzeReportResponse)
async def analyze_report_endpoint(
    file: UploadFile = File(...),
    reading_level: Literal["simple", "detailed"] = Form("simple"),
) -> AnalyzeReportResponse:
    settings = get_settings()
    return AnalyzeReportResponse(
        report_id=str(uuid.uuid4()),
        report_type="Stub report",
        patient_context=PatientContext(),
        summary=ReportSummary(
            overview="Report analysis is not implemented yet.",
            counts=StatusCounts(total=0, normal=0, low=0, high=0, unknown=0),
        ),
        tests=[],
        doctor_questions=[],
        disclaimer=DISCLAIMER,
        meta=AnalyzeMeta(
            pages=0, extraction_method="none", model=settings.GROQ_MODEL, processing_ms=0
        ),
    )
