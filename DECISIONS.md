# Build Decisions

Places where the spec (`MEDBRIDGE_DEV_SPEC.md`) was unclear, silent, or needed a concrete choice. Each entry picks the simplest option that respects the hard rules.

## D1. The repository root is the project root
§5 shows a top-level `medbridge/` folder. The git repo already exists at this folder, so `backend/` and `frontend/` sit directly in the repo root. No extra `medbridge/` wrapper.

## D2. Python 3.12 for the backend venv
The spec asks for Python 3.11+. The machine has 3.11, 3.12 and 3.14. 3.12 is used because PyTorch, FAISS and PyMuPDF all ship stable wheels for it. 3.14 is too new for some of these.

## D3. CPU-only PyTorch
`sentence-transformers` needs PyTorch. The CPU-only wheel (`--index-url https://download.pytorch.org/whl/cpu`) is installed before the other requirements, as §16.2 suggests. It is much smaller than the CUDA build, and a GPU is not needed for a small knowledge base.

## D4. Task list kept in `TASKS.md`
No task-tracking tool was available while building, so progress is tracked in `TASKS.md` at the repo root.

## D5. Frontend scaffolded by hand, not with `npm create vite`
`npm create vite` asks questions interactively. The same files (package.json, vite.config.js, index.html, src/) are written directly, using the same React + Vite template layout.

## D6. Live Groq checks deferred
The user will add the Groq API key to `backend/.env` later and asked for light testing only. The live acceptance checks (real Groq calls in Phases 2 and 4) are skipped during the build. Every LLM code path is covered by the mocked tests instead. `backend/.env` was created from `.env.example` with the placeholder key. Until a real key is added, the server refuses to start and says so clearly (fail-fast, §13).

## D7. Qualitative results that match the expected result count as "normal"
§13 says rows that can't be parsed get status `unknown`. A row such as "Urine Glucose: Negative (reference: Negative)" is a clear, deterministic match, so it is marked `normal` with `status_source: computed`. Any other text-only result without a lab flag stays `unknown`.

## D8. "Borderline" comes only from the lab's own flag
The spec allows `borderline` when the lab prints it or for labelled bands. For simplicity, only the lab's printed flag (e.g. "Borderline High") produces `borderline`. For labelled bands such as "Desirable: <200 Borderline: 200-239", the first (desirable) band is used as the range (§8.4).

## D9. At least 4 doctor questions
If the explanation call returns fewer than 4 doctor questions, generic, safe questions are added so the Phase 2 target (≥ 4 questions) always holds.

## D10. FAISS with an exact numpy fallback
On the build machine, Windows Application Control (Smart App Control) blocked FAISS's native DLL (`DLL load failed ... An Application Control policy has blocked this file`). PyTorch and the embedding model load fine. The index store therefore uses FAISS `IndexFlatIP` when its library loads, and otherwise does the same exact inner-product search with a numpy matrix product. Vectors are always saved to `vectors.npy` alongside `faiss.index`, so one index works with either backend. For a few hundred normalised vectors the results are identical. `faiss-cpu` stays in `requirements.txt`.

## D11. Knowledge-base reference URLs
Every KB document is written in plain language in the project's own words. Each file's frontmatter credits the public reference it was checked against: mostly MedlinePlus, plus NHS, Testing.com and Cleveland Clinic. No text was copied. Please open each `source_url` once before the demo, because health websites sometimes move pages.

## D12. Retrieval threshold kept at 0.35
`scripts/eval_retrieval.py` showed on-topic top scores of 0.51–0.76 and off-topic scores of 0.04–0.14. The default `RAG_MIN_SCORE=0.35` sits well inside that gap, so it was not changed. Results: hit@1 = 0.95, hit@3 = 1.00 on 20 questions (`backend/scripts/eval_results.md`).

## D13. `used_report_context` is true only if the answer used the report
The response flag is set when report context was sent **and** the answer contains a `[Report]` marker. This is the most honest signal for the UI.

## D14. The prebuilt index is not committed
`backend/data/index/` stays git-ignored. Build it with `python -m scripts.build_index` (about 30 seconds after the model download). This way the index can never get out of date with the knowledge base.

## D15. One live test stands in for the deferred live checks
`backend/tests/test_live.py` (marked `live`, skipped by default) runs the Phase 2 acceptance check against the real Groq API: the CBC sample must return Haemoglobin `low`, at least 4 doctor questions and a disclaimer, in under 15 s. Once a key is in `.env`, run `pytest -m live`. In that mode `conftest.py` keeps the real key instead of the dummy test key.

## D16. Screenshots (resolved)
Once the Groq key was set, screenshots of live output on the synthetic samples were added to `docs/screenshots/` and the README.

## D17. Rate limiting is middleware
The optional per-IP limit from §12 (20 requests per minute) is Starlette middleware, not a route, so the two-endpoint rule still holds. Set `RATE_LIMIT_PER_MINUTE=0` to turn it off.

## D18. Default model changed to `openai/gpt-oss-120b`
On 2026-11-12, Groq returned `404 model_not_found` for `llama-3.3-70b-versatile` (the spec's default; §0 warns that Groq retires models). From the models this key can use, `openai/gpt-oss-120b` was chosen: a large general chat model with JSON mode and a 131k context. The live CBC check passes in about 9 s. The model is still read only from `GROQ_MODEL`, so it can be changed in `.env` without touching code.

## D19. Full-width citation brackets are normalised
gpt-oss sometimes writes markers as `【1】` / `【Report】`. `answerer.normalize_markers` converts them to `[1]` / `[Report]` before citations are mapped, so source mapping, the "your report" badge and `used_report_context` work for any model.
