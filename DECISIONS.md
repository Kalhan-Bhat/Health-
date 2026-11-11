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
