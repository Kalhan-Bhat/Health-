"""POST /api/ask — Feature F2 (knowledge assistant with RAG)."""

import time

from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.errors import AppError
from app.safety import guardrails
from app.schemas import AskRequest, AskResponse
from app.services.rag import answerer, retriever
from app.services.rag.index_store import store

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest) -> AskResponse:
    """Answer a question about lab tests using the curated knowledge base, with sources."""
    started = time.perf_counter()
    question = req.question.strip()
    if len(question) < 3:
        raise AppError("INVALID_QUESTION", 400, "Please type a question of at least 3 characters.")

    # Emergencies never reach the LLM.
    if guardrails.is_emergency_question(question):
        return answerer.emergency_response(started=started)

    if not store.ready:
        raise AppError("INDEX_NOT_READY", 503, "The knowledge base is not available right now.")

    # Embedding is CPU work, so run it off the event loop.
    hits = await run_in_threadpool(retriever.retrieve, question, req.report_context)
    return await answerer.answer(req, hits, started=started)
