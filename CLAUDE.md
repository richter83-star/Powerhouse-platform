# CLAUDE.md — Powerhouse Multi-Agent Platform

---

## Stack

FastAPI (Python 3.11) backend · Next.js 14 App Router frontend · PostgreSQL 15 (SQLite for local dev) · Redis 7 · Prisma (frontend ORM) · Alembic (backend migrations) · Docker Compose · Kubernetes

---

## Non-obvious Conventions

### Backend entry points
- `api/main.py` — production / Docker (always use this)
- `api/server.py` — minimal dev server only
- `api.py` / `app.py` at the repo root are legacy stubs; do not use

### Agent system
- All agents live in `backend/agents/` and are **auto-discovered at startup** — no registration needed
- Every agent must inherit `core.base_agent.BaseAgent` and implement `async execute(task, context) -> dict`
- `agents_backup/` contains legacy snapshots — do not modify; excluded from linting

### Where new code goes
- New API routes → `backend/api/routes/` then register in `backend/api/main.py`
- New agents → `backend/agents/` (auto-discovered)
- New frontend pages → `frontend/app/app/` (Next.js App Router)
- DB schema changes → Alembic migration (backend) **and/or** Prisma migration (frontend)

### Frontend
- Strict TypeScript (`"strict": true`)
- Use `@/*` for all intra-app imports
- After changing backend routes, regenerate the TS client: `npm run generate:api` (runs `openapi-typescript` against `/openapi.json`)
- ESLint errors **block** builds — `typescript.ignoreBuildErrors: false`

### Migrations
- Alembic runs automatically on backend startup — a bad `DATABASE_URL` causes a hard crash, not a graceful degradation
- For local dev, SQLite is fine: `DATABASE_URL=sqlite:///./powerhouse.db`

### Tests
- Only `tests/test_smoke.py` is reliably runnable without Docker/external services
- E2E and integration tests (`test_e2e.py`, `test_*_e2e.py`, etc.) require live Postgres + Redis

### Dependencies
- `requirements-minimal.txt` omits `torch`, `kafka-python`, `nats-py`, and other heavy ML libs — use it for quick local starts
- `bcrypt<4.0.0` is pinned intentionally (passlib 1.7.4 compatibility); do not upgrade

---

## Environment Files

Three separate env files — do not conflate them:

| File | Consumed by |
|---|---|
| `.env` (repo root) | docker-compose (all services) |
| `backend/.env` | local backend dev |
| `frontend/app/.env.local` | local frontend dev |

Key variables an AI needs to know exist:
- `LLM_ALLOW_NO_KEY=true` — lets the backend start without an LLM key
- `SECRET_KEY` / `JWT_SECRET_KEY` — must be changed before any production deploy
- `NEXT_PUBLIC_API_URL` — browser-side API URL (default `http://localhost:8001`)
- `BACKEND_INTERNAL_URL` — SSR-side API URL (default `http://backend:8000`)

---

## Quick Commands

```bash
# Start everything (recommended)
docker-compose up -d

# Backend local dev
cd backend && uvicorn api.main:app --reload --port 8001

# Frontend local dev
cd frontend/app && npm run dev

# Backend smoke test (no infra needed)
cd backend && pytest tests/test_smoke.py -v

# New Alembic migration
cd backend && alembic revision --autogenerate -m "description"

# Regenerate frontend API types
cd frontend/app && npm run generate:api
```

---

## Security Rules
- Never hardcode secrets — env vars only
- Pydantic validates all inputs at API boundaries
- Multi-tenant: every DB query must be scoped to tenant ID
