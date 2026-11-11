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
| 6 | Hardening & polish: rate limit, post-check, logging, print CSS, a11y, README, lint clean, DoD | ⏳ In progress |
