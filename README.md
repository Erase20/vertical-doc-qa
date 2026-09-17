# Vertical Document QA

Initial framework for a vertical-domain document question answering assistant.

## Documentation

- [Development dossier](DEVELOPMENT_DOSSIER.md): requirements, architecture, APIs, data model, testing and roadmap.
- [Development record](DEVELOPMENT_RECORD.md): completed work, deployment history, current status and next steps.
- [Psychology redevelopment plan](PSYCHOLOGY_REDEVELOPMENT.md): minimum domain adaptation plan for psychoeducation, assessment guidance and professional reference retrieval.

## Services

- `web`: Next.js upload and chat interface.
- `api`: FastAPI REST and SSE service.
- `worker`: Celery worker for document processing.
- `postgres`: PostgreSQL with pgvector.
- `redis`: Celery broker and short-lived application state.

## Start

```bash
cp .env.example .env
docker compose up --build
```

PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- Web: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

The default environment starts the complete framework without external model
credentials. Upload and chat endpoints are wired, while model-backed indexing
and generation require `EMBEDDING_API_KEY` and `LLM_API_KEY`.

## Local development

Backend:

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

The API and worker expect PostgreSQL and Redis. Docker Compose is the supported
way to run those dependencies.

## Zero-cost interview demo

Set `DEMO_MODE=true` to run the complete upload, indexing, retrieval, streaming
answer and citation flow without model credentials. The demo uses deterministic
local embeddings and an extractive answer generator; it does not call an
external LLM.

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for deployment and presentation steps.

```dotenv
DEMO_MODE=true
```

Start or restart the API and worker:

```bash
docker compose up -d --build api worker
```

To switch back to a real model, set `DEMO_MODE=false`, configure the LLM and
embedding credentials, and rebuild. Existing chunks must be reindexed when
changing between demo and real embeddings.
