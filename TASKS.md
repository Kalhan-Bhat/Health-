# MedBridge — Build Task List

Tracks progress through the phased build plan (spec §15). Updated at the end of each phase.

| Phase | Description | Status |
|---|---|---|
| 0 | Scaffolding: repo structure, .gitignore, backend venv, FastAPI with 2 stub routes, Vite React shell (tabs, DisclaimerBanner, proxy), `test_routes.py` | ✅ Done |
| 1 | PDF extraction: `make_sample_pdfs.py`, `pdf_extractor.py`, error envelope + handlers, `test_pdf_extract.py` | ✅ Done |
| 2 | Report analysis with LLM: `llm_client.py`, prompts, `range_parser.py`, `report_analyzer.py`, red flags, tests | ✅ Done (live Groq check deferred, see DECISIONS D6) |
| 3 | Frontend report experience: upload, summary, explanation cards, doctor questions, dashboard + range bars | ✅ Done |
| 4 | Knowledge base (≥25 docs) + RAG: chunker, embedder, index, retriever, answerer, eval (hit@3 ≥ 0.8) | ✅ Done (30 docs; hit@3 = 1.00) |
| 5 | Ask tab UI + report-aware Q&A: chat, source cards, citations, suggestions, report toggle | ✅ Done |
| 6 | Hardening & polish: rate limit, post-check, logging, print CSS, a11y, README, lint clean, DoD | ✅ Done |

## Definition of Done (spec §18)

| Item | Result |
|---|---|
| Exactly two application endpoints, enforced by `test_routes.py` | ✅ 4/4 route tests pass; `/docs` lists only the 2 POST routes |
| All three features work end-to-end on the three sample PDFs | ⚠️ Verified with a mocked LLM and a real-server smoke test. Live run pending the user's Groq key (`pytest -m live`, then the demo) |
| Every AI response includes the disclaimer; KB answers include sources or the no-answer state | ✅ Enforced by the response schemas and covered by tests |
| No user report data persisted or logged | ✅ In-memory processing; every log call audited (sizes, latency and token counts only) |
| `pytest` passes; `npm run build` passes; linters clean | ✅ 122 backend + 12 frontend tests; ruff and eslint clean; build OK |
| Retrieval eval hit@3 ≥ 0.8 documented | ✅ hit@3 = 1.00, hit@1 = 0.95 (`backend/scripts/eval_results.md`, README) |
| README: overview, architecture, setup, env vars, screenshots, limitations, disclaimer, credits | ✅ Done. Screenshots to be added once the Groq key is set (DECISIONS D16) |
| Demo script runs 3× consecutively without failure | ⏳ Needs the Groq key. Skipped at the user's request (light testing) |
