"""POST /api/analyze-report — Feature F1 (report explanation)."""

import time
from typing import Literal

from fastapi import APIRouter, File, Form, UploadFile

from app.config import get_settings
from app.schemas import AnalyzeReportResponse
from app.services import report_analyzer
from app.services.pdf_extractor import read_capped, validate_and_extract

router = APIRouter()


@router.post("/analyze-report", response_model=AnalyzeReportResponse)
async def analyze_report_endpoint(
    file: UploadFile = File(...),
    reading_level: Literal["simple", "detailed"] = Form("simple"),
) -> AnalyzeReportResponse:
    """Upload a text-based lab report PDF and get a plain-language explanation.

    The file is processed in memory only and is never stored.
    """
    started = time.perf_counter()
    settings = get_settings()
    data = await read_capped(file, settings.MAX_UPLOAD_MB)
    extracted = validate_and_extract(data, file.filename, file.content_type)
    del data  # the raw upload is no longer needed
    return await report_analyzer.analyze_report(extracted, reading_level, started=started)
