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
