# PensionOS Backend (FastAPI) - Minimal scaffold

Run the development server (from repo root) after installing dependencies:

```bash
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Available (minimal) endpoints:
- `GET /health` - health check
- `GET /sources` - list registered sources
- `POST /sources` - register a source (JSON body)
- `POST /batches` - create a batch (JSON body)
- `GET /mapping/packs?source_type=...` - list mapping packs for a source type
- `POST /mapping/suggestions` - register a mapping suggestion
