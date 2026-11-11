"""POST /api/analyze-report — Feature F1 (report explanation).

Phase 1: validates the upload and extracts text; the LLM analysis is still a stub.
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
from app.services.pdf_extractor import read_capped, validate_and_extract

router = APIRouter()


@router.post("/analyze-report", response_model=AnalyzeReportResponse)
async def analyze_report_endpoint(
    file: UploadFile = File(...),
    reading_level: Literal["simple", "detailed"] = Form("simple"),
) -> AnalyzeReportResponse:
    settings = get_settings()
    data = await read_capped(file, settings.MAX_UPLOAD_MB)
    extracted = validate_and_extract(data, file.filename, file.content_type)
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
            pages=extracted.pages,
            extraction_method=extracted.method,
            model=settings.GROQ_MODEL,
            processing_ms=0,
        ),
    )
