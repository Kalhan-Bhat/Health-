"""POST /api/ask — Feature F2 (knowledge assistant with RAG).

Phase 0: returns a stub response that already matches the response model.
"""

from fastapi import APIRouter

from app.config import get_settings
from app.safety.disclaimers import DISCLAIMER
from app.schemas import AskMeta, AskRequest, AskResponse

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest) -> AskResponse:
    settings = get_settings()
    return AskResponse(
        answer="The knowledge assistant is not implemented yet.",
        grounded=False,
        sources=[],
        used_report_context=req.report_context is not None,
        disclaimer=DISCLAIMER,
        meta=AskMeta(model=settings.GROQ_MODEL, retrieved=0, processing_ms=0),
    )
