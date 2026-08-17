# PensionOS Data Onboarding — Scaffold

This repository contains a focused scaffold of the PensionOS Data Onboarding slice (PR-01+PR-02 beginnings).

Workspaces:
- `backend/` — FastAPI minimal scaffold that wires in-memory domain services for quick local dev.
- `frontend/` — Next.js minimal scaffold that proxies to the backend for demo pages.

Run backend:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```
# PensionOS Data Onboarding & Resolution Factory

This repository is the working implementation foundation for the PensionOS Data Onboarding & Resolution Factory specification.

## Scope in this slice

The initial slice implements PR-01 only:

- `OnboardingSource`
- `SourceAuthorityPolicy` skeleton
- `OnboardingBatch`
- batch status lifecycle
- repository ports
- domain validation

This intentionally excludes parsing, AI, DQ, exception engines, and final promotion logic.

## Repository layout

- `data_onboarding/` — domain model, ports, and service layer for the first bounded slice
- `tests/` — unit tests for the domain and repository contracts
- `.github/agents/` — agent prompts that guide iterative delivery against the requirements
- `skills/` — Copilot skills for project-specific working practices

## Working rules

- Configure, do not customise.
- Prefer approved rules and explicit data states over silent defaults.
- Treat material pension values as governed data, not auto-corrected guesses.
- Keep provenance and evidence first-class concepts.

## Local validation

```bash
python -m pytest -q
```
