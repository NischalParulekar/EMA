# EMA — Emotional Memory Agent

An AI agent framework with **persistent, emotionally-tagged memory**. Every interaction is scored on a PAD (Pleasure-Arousal-Dominance) emotional vector, blended into a running mood state, and stored for semantic recall — with a canary-token grounding layer that silently detects and recovers from identity drift / hallucination.

The reasoning brain is the **Claude API** (`claude-sonnet-4-6` / `claude-haiku-4-5`). The architecture is model-agnostic — only the LLM call changes if you later swap in a local model.

> Phase 1 implementation. Later phases (forgetting curve, skill crystallization, personality anti-drift, Theory of Mind, routing) are intentionally not built yet.

---

## Features

- **Persistent cross-session memory** — interactions stored via Mem0 + Qdrant
- **Emotional tagging** — each memory carries a PAD vector
- **Running mood state** — PAD mood persists in Redis and shifts per interaction
- **Grounding verification** — canary tokens detect identity drift and recover silently
- **Emotional RAG** — memory retrieval reranked by emotional similarity to current mood
- **Basic model routing** — Haiku vs. Sonnet based on emotional state / message length

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (async) + Pydantic v2 |
| Memory store | Mem0 (self-hosted) |
| Vector DB | Qdrant |
| Relational DB | PostgreSQL (async via asyncpg / SQLAlchemy) |
| Cache / mood | Redis |
| LLM | Anthropic Claude API |
| Frontend | React + Vite |
| Infra | Docker Compose |

---

## Project layout

```
EMA/
├── docker-compose.yml      # Qdrant + Postgres + Redis
├── requirements.txt
├── .env.example            # copy to .env and fill in
├── backend/
│   ├── main.py             # FastAPI app + startup
│   ├── config.py           # Pydantic settings (reads .env)
│   ├── models/             # Pydantic + SQLAlchemy models
│   ├── routers/            # /chat, /mood, /memories
│   ├── services/           # emotional, mood, grounding, memory, llm
│   └── db/                 # async engine + session
└── frontend/               # React + Vite chat UI
```

---

## Prerequisites

- Python 3.11+ (this checkout was built and run on Python 3.14)
- Node.js 18+
- Docker Desktop (running)
- An Anthropic API key

---

## Setup & run

All commands are run from the repo root (`EMA/`).

**1. Start infrastructure**

```bash
docker compose up -d        # qdrant, postgres, redis
docker compose ps           # all three should show Up
```

**2. Configure environment**

```bash
cp .env.example .env        # then edit .env and set ANTHROPIC_API_KEY
```

**3. Backend**

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

**4. Frontend**

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET`  | `/health` | Liveness check |
| `POST` | `/chat/` | Full EMA pipeline: mood → memory → LLM → grounding → mood update |
| `GET`  | `/mood/{user_id}` | Current PAD mood + label |
| `POST` | `/memories/search` | Semantic + emotional memory search |

---

## Environment variables

See [`.env.example`](.env.example). Key ones:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API auth (**required** for `/chat`) |
| `POSTGRES_URL` | Async Postgres DSN |
| `REDIS_URL` | Redis connection |
| `QDRANT_URL` | Qdrant connection |
| `MEM0_COLLECTION` | Mem0 / Qdrant collection name |
| `CANARY_PREFIX` | Prefix for grounding canary tokens |

---

## Notes & known limitations

- **`/chat` requires a real `ANTHROPIC_API_KEY`** — with the placeholder it returns a 500 at the LLM call.
- **Mem0 memory is disabled until a valid embedder is configured.** The default config in `backend/services/memory_service.py` references an `anthropic` / `voyage-3` embedder, which is not a valid Mem0 embedding provider (Anthropic has no embeddings API). Memory storage/retrieval degrades gracefully (the rest of the pipeline still works); point the embedder at a real provider (e.g. `openai` or `voyageai`) with its key to enable persistence.
- **Dependency pins** in `requirements.txt` use `>=` floors so they resolve on newer Python (3.14). The original plan used exact pins that lack 3.14 wheels.
