# CLAUDE.md — Powerhouse Multi-Agent Platform

Guidance for AI assistants working in this repository.

---

## Project Overview

**Powerhouse** is an enterprise-grade multi-agent AI platform for B2B use cases. It orchestrates 19+ specialized AI agents to solve complex business challenges.

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python 3.11+) |
| Frontend | Next.js 14 (React 18, TypeScript) |
| Desktop | Electron wrapper |
| Database | PostgreSQL 15 (SQLite for local dev) |
| Cache / Queue | Redis 7 |
| ORM (frontend) | Prisma 6 |
| Migrations (backend) | Alembic |
| Containerization | Docker Compose |
| Orchestration | Kubernetes (k8s/) |

---

## Repository Layout

```
Powerhouse-platform/
├── backend/               # FastAPI Python backend
│   ├── agents/            # 19+ agent implementations (auto-discovered)
│   ├── api/               # Route modules and FastAPI app entry points
│   │   ├── main.py        # Primary entry point (docker / production)
│   │   ├── server.py      # Minimal server (development)
│   │   └── routes/        # Feature-specific route files
│   ├── core/              # Orchestrator, base_agent, communication, plugins
│   │   ├── orchestrator.py
│   │   ├── base_agent.py
│   │   ├── agent_loader.py
│   │   └── ...            # 40+ core modules
│   ├── config/            # Settings (pydantic-settings), default.json
│   ├── database/          # SQLAlchemy models, session, Alembic migrations
│   ├── communication/     # Message bus, agent registry, shared context
│   ├── tests/             # pytest test suite (40+ test files)
│   ├── requirements.txt   # Full dependency list
│   ├── requirements-minimal.txt  # Lighter set for quick local starts
│   ├── Dockerfile         # Production image (python:3.11-slim)
│   └── .env.example       # Environment variable template
├── frontend/
│   └── app/               # Next.js application
│       ├── app/           # Next.js App Router pages
│       ├── components/    # Shared React components
│       ├── contexts/      # React context providers
│       ├── hooks/         # Custom hooks
│       ├── prisma/        # Prisma schema and seed scripts
│       ├── types/         # TypeScript type definitions
│       ├── next.config.js
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── package.json
├── electron-app/          # Electron desktop wrapper
├── bridge/                # Bridge service
├── grafana/               # Grafana dashboards
├── k8s/                   # Kubernetes manifests
├── scripts/               # Utility and maintenance scripts
├── docs/                  # Architecture, deployment, and user guides
├── docker-compose.yml     # Development / standard compose
├── docker-compose.prod.yml
├── docker-compose.fast.yml
└── install_powerhouse.py  # Automated installer
```

---

## Development Workflows

### Quickest Local Start (Docker-only — recommended)

```bash
# Requires only Docker Desktop
docker-compose up -d
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# Swagger docs: http://localhost:8001/docs
```

### Backend Local Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Minimal install (avoids heavy ML downloads)
pip install -r requirements-minimal.txt
# Full install
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env as needed. For SQLite quick-start:
export DATABASE_URL=sqlite:///./powerhouse.db

# Start dev server (reloads on change)
uvicorn api.main:app --reload --port 8001
# or the simpler server:
uvicorn api.server:app --reload
```

### Frontend Local Development

```bash
cd frontend/app
npm install           # also runs `prisma generate` via postinstall
npm run dev           # starts on http://localhost:3000
```

### Environment Variables

**Backend** — copy `backend/.env.example` → `backend/.env`:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | DB connection string | `sqlite:///./powerhouse.db` |
| `SECRET_KEY` | JWT signing key | *must change in prod* |
| `JWT_SECRET_KEY` | JWT access/refresh tokens | *must change in prod* |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `OPENAI_API_KEY` | OpenAI LLM provider | — |
| `ANTHROPIC_API_KEY` | Anthropic LLM provider | — |
| `LLM_PROVIDER` | Override default provider | — |
| `LLM_ALLOW_NO_KEY` | Allow offline runs without a key | `false` |
| `MEMORY_STORE_PATH` | Persist MetaMemoryAgent entries | — |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `DEBUG` | Enable debug mode | `false` |
| `SENTRY_DSN` | Sentry error reporting | — |

**Root `.env`** (used by docker-compose for all services):

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | PostgreSQL credentials |
| `REDIS_PASSWORD` | Redis auth password |
| `SECRET_KEY` / `JWT_SECRET_KEY` / `NEXTAUTH_SECRET` | Application secrets |
| `S3_BUCKET` / `S3_REGION` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS S3 file storage |
| `MARKETPLACE_CURRENCY` | Default marketplace currency |

**Frontend** — `frontend/app/.env.local`:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | Prisma DB URL | — |
| `NEXTAUTH_URL` | NextAuth base URL | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Backend API URL exposed to browser | `http://localhost:8001` |
| `BACKEND_INTERNAL_URL` | SSR requests to backend | `http://backend:8000` |

---

## Testing

### Backend Tests (pytest)

```bash
cd backend

# Run a fast smoke check (no external services needed)
pytest tests/test_smoke.py -v

# Run API health tests only
pytest tests/test_api_endpoints.py -k health -v

# Run a specific test file
pytest tests/test_agents_phase1.py -v

# Full suite (may require DB / external services)
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

Key test files:
- `tests/test_api_endpoints.py` — HTTP endpoint integration tests
- `tests/test_agents_phase1.py` — Core agent behaviour
- `tests/test_communication_protocol.py` — Message bus / registry
- `tests/test_auth.py` — Authentication flows
- `tests/test_security.py` — Security checks
- `tests/test_smoke.py` — Lightweight health checks

### Frontend Tests

```bash
cd frontend/app
npm test
```

---

## Build & Lint

### Frontend

```bash
cd frontend/app
npm run lint          # ESLint + eslint-config-next
npm run build         # Next.js production build
npm run generate:api  # Regenerate TypeScript types from OpenAPI spec (openapi-typescript)
```

ESLint is configured via `eslint-config-next` with TypeScript support (`@typescript-eslint`). ESLint errors are **not** ignored during builds (`typescript.ignoreBuildErrors: false` in `next.config.js`). Prettier is integrated via `eslint-plugin-prettier`.

### Backend

```bash
cd backend
# Linting (flake8, max line length 127, max complexity 10)
flake8 .

# Formatting
black .

# Security scan
bandit -r .

# Dependency vulnerability check
safety check
```

Flake8 config is in `.flake8` (excludes `agents_backup`). Strict enforcement: E9, F63, F7, F82 error codes.

### Electron App

```bash
cd electron-app
npm start        # Launch in dev
npm run pack     # Package without installer
npm run dist     # Build full Windows installer (NSIS)
npm run dist-win # Windows x64 build
# Output: electron-app/dist/Powerhouse Setup 1.0.0.exe
```

---

## CI/CD (GitHub Actions)

Workflows live in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `backend-ci.yml` | Push/PR to `main`/`develop` touching `backend/**` | pytest, flake8, black, bandit, safety check, Codecov upload |
| `frontend-ci.yml` | Push/PR to `main`/`develop` touching `frontend/**` | eslint, tsc, `npm run build`, OpenAPI drift detection, npm audit |
| `code-quality.yml` | Continuous | Code quality checks |
| `deploy-staging.yml` | — | Staging deployment |
| `deploy-production.yml` | — | Docker push + production deployment |
| `security-scan.yml` | — | Dedicated security scanning |

**Test matrix (backend CI)**: Python 3.11, PostgreSQL 15, Redis 7.

---

## Architecture

### System Layers

```
Client (Browser / Electron)
        │
        ▼
  Next.js Frontend (port 3000)
        │ REST API calls
        ▼
  FastAPI Backend (port 8001)
        │
        ├── Orchestrator
        │       │  Dynamic agent loading (AgentLoader)
        │       │  Sequential / parallel / adaptive execution
        │       └── Retry logic, error handling
        │
        ├── Agent Pool (19+ agents in backend/agents/)
        │       │  All inherit from BaseAgent
        │       │  Auto-discovered at startup
        │
        ├── Communication Protocol
        │       ├── MessageBus   (routing, queuing, history)
        │       ├── AgentRegistry (discovery, health, load balancing)
        │       └── SharedContext (global + per-agent namespaced state)
        │
        └── Infrastructure
                ├── PostgreSQL / SQLite (SQLAlchemy + Alembic)
                ├── Redis (cache, queues)
                └── LLM Abstraction (OpenAI, Anthropic, custom)
```

### Execution Strategies

The `Orchestrator` supports three modes:

1. **Sequential** — agents run one after another, each feeding results to the next
2. **Parallel** — agents run simultaneously and results are aggregated
3. **Adaptive** — dynamic execution path chosen based on agent outputs

### Multi-tenancy

- `Tenant` → `Project` → `Run` → `AgentRun` / `AgentMessage` (database hierarchy)
- Tenant ID is scoped on all DB queries
- UUID primary keys throughout

---

## Agent System

### Adding a New Agent

1. Create `backend/agents/my_agent.py`
2. Inherit from `core.base_agent.BaseAgent`
3. Implement the `execute()` method
4. Define `CAPABILITIES` class attribute
5. The agent is **auto-discovered** at startup — no registration required

```python
from core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    CAPABILITIES = ["my-capability"]

    def __init__(self, *args, **kwargs):
        super().__init__(name="my_agent", agent_type="custom", *args, **kwargs)

    async def execute(self, task: str, context: dict) -> dict:
        # implement logic here
        return {"result": "..."}
```

### Available Agents (backend/agents/)

| File | Description |
|---|---|
| `react.py` | ReAct reasoning-action loop |
| `evaluator.py` / `evaluator_agent.py` | Output evaluation |
| `reflection.py` | Self-reflection and improvement |
| `chain_of_thought.py` | CoT reasoning |
| `tree_of_thought.py` | Tree-of-thought exploration |
| `planning.py` | Task planning |
| `debate.py` | Multi-agent debate |
| `swarm.py` | Swarm intelligence |
| `memory_agent.py` | Persistent memory |
| `adaptive_memory.py` | Adaptive memory management |
| `curriculum_agent.py` | Curriculum-based learning (supports `seed=`) |
| `meta_evolver.py` | Meta-evolution hooks (supports `seed=`) |
| `governor.py` | Policy enforcement |
| `voyager.py` | Exploration agent |
| `hierarchical_agents.py` | Hierarchical multi-agent coordination |
| `generative_agents.py` | Generative agent behaviours |
| `toolformer.py` | Tool-use agent |
| `multi_agent.py` | Multi-agent orchestration |
| `auto_loop_agent.py` | Autonomous looping agent |

---

## Database

### Backend (SQLAlchemy + Alembic)

- Models live in `backend/database/models.py`
- Session management in `backend/database/session.py`
- Migrations are run automatically on startup via Alembic
- For local dev SQLite is the default; PostgreSQL is required for production

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend (Prisma)

- Schema: `frontend/app/prisma/schema.prisma`
- Provider: PostgreSQL
- Key models: `User`, `Account`, `Session`, `VerificationToken`, `Workflow`

```bash
cd frontend/app
npx prisma generate        # regenerate client (also runs on npm install)
npx prisma migrate dev     # create and apply a new migration
npx prisma db seed         # seed with test data (uses scripts/seed.ts)
npx prisma studio          # open DB GUI
```

---

## API Reference

### Backend Entry Points

| Entry point | Used by |
|---|---|
| `api/main.py` | Docker / production (`uvicorn api.main:app`) |
| `api/server.py` | Minimal development server |

### Core Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/task` | Submit a task to the agent orchestrator |
| `GET/POST` | `/api/v1/auth/*` | Authentication |
| `GET/POST` | `/api/v1/workflows/*` | Workflow management |
| `GET/POST` | `/api/v1/agents/*` | Agent management |
| `GET/POST` | `/api/v1/billing/*` | Billing / subscriptions |
| `GET/POST` | `/api/v1/marketplace/*` | Agent marketplace |

Full interactive docs available at `http://localhost:8001/docs` (Swagger UI).

---

## Docker

### Services (docker-compose.yml)

| Service | Image | Internal port | Host port |
|---|---|---|---|
| `postgres` | postgres:15-alpine | 5432 | 5434 |
| `redis` | redis:7-alpine | 6379 | 6379 |
| `backend` | ./backend/Dockerfile | 8000 | 8001 |
| `frontend` | ./frontend/app/Dockerfile | 3000 | 3000 |

### Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Production variant
docker-compose -f docker-compose.prod.yml up -d
```

### Backend Docker Image

- Base: `python:3.11-slim`
- Runs as non-root user `appuser`
- 4 uvicorn workers
- Starts with: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4`

---

## Security Conventions

- JWT-based authentication (HS256 algorithm, configurable expiry)
- RBAC (role-based access control) with multi-tenant isolation
- All secrets via environment variables — **never hardcode credentials**
- `SECRET_KEY` and `JWT_SECRET_KEY` must be changed before production deployment
- Pydantic models validate all inputs at API boundaries
- Audit logging for all operations
- CORS origins controlled via `cors_origins` setting

---

## Conventions for AI Assistants

### Code Style

- **Python**: Follow PEP 8. All new agents must inherit from `BaseAgent`. Use pydantic models for data validation. Prefer async functions for I/O-bound work.
- **TypeScript/React**: Strict TypeScript (`"strict": true`). Use the `@/*` alias for imports within the frontend. Tailwind CSS for styling with Radix UI components.
- **No hardcoded secrets** — always use environment variables.

### Adding Features

- New API routes go in `backend/api/routes/` and are registered in `backend/api/main.py`
- New agents go in `backend/agents/` inheriting `BaseAgent` (auto-discovered)
- New frontend pages go in `frontend/app/app/` following Next.js App Router conventions
- DB schema changes require both an Alembic migration (backend) and/or Prisma migration (frontend)

### Testing

- Write pytest tests for new backend features in `backend/tests/`
- Prefer isolated unit tests; use `httpx.AsyncClient` with `TestClient` for API tests
- Use `conftest.py` for shared fixtures

### Git Workflow

- Work on feature branches
- The production entry point for the backend is `api/main.py` (not `api/server.py`)
- Environment-specific config belongs in `.env` files, not committed to the repo

---

## Key Documentation Files

| File | Content |
|---|---|
| `backend/ARCHITECTURE.md` | Detailed system architecture diagrams |
| `backend/AGENT_IMPLEMENTATION_SUMMARY.md` | Agent implementation reference |
| `docs/DEPLOYMENT_GUIDE.md` | Production deployment steps |
| `docs/ARCHITECTURE.md` | High-level system design |
| `docs/TROUBLESHOOTING.md` | Common issues and fixes |
| `docs/USER_GUIDE.md` | End-user documentation |
| `backend/QUICKSTART.md` | Backend quick-start guide |

---

## Access Points (when running locally)

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8001 |
| Swagger UI | http://localhost:8001/docs |
| PostgreSQL | localhost:5434 |
| Redis | localhost:6379 |
