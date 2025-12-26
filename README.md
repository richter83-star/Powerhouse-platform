# Powerhouse Multi-Agent Platform

Enterprise-grade multi-agent AI platform for B2B use cases. Orchestrates 19+ specialized AI agents to solve complex business challenges.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with multi-agent orchestrator
- **Frontend**: Next.js 14 (React 18, TypeScript)
- **Database**: PostgreSQL 15
- **Desktop**: Electron wrapper for standalone deployment
- **Infrastructure**: Docker Compose for containerization

## 📝 Changelog (Unreleased)

- Added agent reflection/evaluation logging with memory-guided planning and swarm consensus voting.
- Added curriculum adaptation, meta-evolution hooks, and a learning-loop test.
- New optional env var: `MEMORY_STORE_PATH` to persist MetaMemoryAgent entries.
- New optional seeds for deterministic behavior: `CurriculumAgent(seed=...)`, `MetaEvolverAgent(seed=...)`.
- Added LLM provider override `LLM_PROVIDER` and local fallback via `LLM_ALLOW_NO_KEY` for offline runs.

## 🚀 Quick Start

### Prerequisites

Before installing, make sure you have:

- **Python 3.11+** - [Download](https://www.python.org/downloads/) (check "Add Python to PATH")
- **Node.js 18+** - [Download](https://nodejs.org/) (LTS version recommended)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/) (for database)
- **Git** (optional, for cloning the repository)

### 🚀 Fast Installation Options

**Choose the fastest method for you:**

#### Option 1: Docker-Only Install (Fastest - Recommended!) ⭐
**File:** `INSTALL_DOCKER_ONLY.bat`  
**Time:** 5-8 minutes (first time), 30 seconds (after)  
**Requirements:** Only Docker Desktop needed (no Python/Node.js!)

**Why this is fastest:**
- ✅ No local dependencies to install
- ✅ Everything runs in containers
- ✅ Images cached for instant future startups
- ✅ One script does everything

**Usage:**
```bash
INSTALL_DOCKER_ONLY.bat
```

#### Option 2: First-Time Setup Wizard
**File:** `SETUP_FIRST_TIME.bat`  
**Time:** 3-5 minutes (first time), 30 seconds (after)  
**Best for:** Users who want step-by-step guidance

**Features:**
- ✅ Automatic prerequisite checking
- ✅ Pre-downloads images for faster startup
- ✅ Helpful error messages
- ✅ Verifies everything works

**Usage:**
```bash
SETUP_FIRST_TIME.bat
```

#### Option 3: Quick Install
**File:** `QUICK_INSTALL.bat`  
**Time:** 2-3 minutes (first time), 30 seconds (after)  
**Best for:** Users who want fast setup with minimal interaction

**Usage:**
```bash
QUICK_INSTALL.bat
```

#### Option 4: Traditional Install (Full Local Setup)
**File:** `INSTALL.bat`  
**Time:** 5-10 minutes  
**Requirements:** Python 3.11+, Node.js 18+, Docker Desktop

**Usage:**
```bash
INSTALL.bat
```

---

### 🎯 Recommended: Docker-Only Install

**For first-time users, we recommend `INSTALL_DOCKER_ONLY.bat`:**

1. **Install Docker Desktop** (if not already installed)
   - Download: https://www.docker.com/products/docker-desktop/
   - Start Docker Desktop and wait for it to fully start

2. **Run the installer:**
   ```bash
   INSTALL_DOCKER_ONLY.bat
   ```

3. **That's it!** Access at http://localhost:3000

**Advantages:**
- No Python or Node.js installation needed
- Faster setup (everything in Docker)
- Easier to maintain
- Works consistently across different systems

> 💡 **See `FIRST_TIME_SETUP.md`** for detailed comparison of all installation methods.

### Alternative: Manual Installation

If you prefer manual steps or encounter issues:

1. **Run Diagnostics** (troubleshooting):
   ```bash
   DIAGNOSE.bat
   ```

2. **Install Dependencies**:
   ```bash
   INSTALL.bat
   ```
   
   Or install backend only:
   ```bash
   scripts\INSTALL_BACKEND_ONLY.bat
   ```

3. **Start Services Individually**:
   ```bash
   1_START_DATABASE.bat    # PostgreSQL (wait for it to finish)
   2_START_BACKEND.bat     # FastAPI (keep window open)
   3_START_FRONTEND.bat    # Next.js (keep window open)
   ```

### Access Points

Once running, access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Database**: localhost:5432 (PostgreSQL)

## 📁 Project Structure

```
POWERHOUSE_DEBUG/
├── backend/          # FastAPI backend
│   ├── agents/       # 19+ AI agent implementations
│   ├── api/          # API routes and endpoints
│   ├── core/         # Core orchestration, security, monitoring
│   ├── database/     # Database models and migrations
│   └── tests/        # Test suite
├── frontend/
│   ├── app/          # Next.js application
│   └── desktop/      # Electron desktop app
├── electron-app/     # Alternative Electron wrapper
└── docker-compose.yml
```

## 🔧 Development

### Backend Development

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# Install dependencies (minimal set to avoid heavy ML downloads)
pip install -r requirements-minimal.txt

# Copy environment template and point the API at a local SQLite DB for quick starts
cp .env.example .env
export DATABASE_URL=${DATABASE_URL:-sqlite:///./powerhouse.db}

# Run development server
uvicorn api.server:app --reload --port 8001
```

### Frontend Development

```bash
cd frontend/app

# Install dependencies (if not already done)
npm install

# Run development server
npm run dev
```

### Environment Variables

**Backend** (`backend/.env`):
- Copy `.env.example` to `.env` and configure:
  - Database connection string
  - JWT secrets
  - API keys (OpenAI, Stripe, etc.)

**Frontend** (`frontend/app/.env.local`):
- Copy `.env.example` to `.env.local` and configure:
  - `NEXT_PUBLIC_API_URL` (default: http://localhost:8001)
  - Authentication settings

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/test_api_endpoints.py -k health -v

# Full suite (may require external services)
# pytest tests/ -v

# Frontend tests
cd frontend/app
npm test
```

## 📚 Documentation

- [Backend Architecture](backend/ARCHITECTURE.md)
- [Agent Implementation Summary](backend/AGENT_IMPLEMENTATION_SUMMARY.md)
- [API Documentation](http://localhost:8001/docs)

## 🔐 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Multi-tenant isolation
- Audit logging
- Rate limiting

## 🚢 Deployment

### Production Installer (Recommended for End Users)

Build a professional Windows installer that creates `Setup.exe` and `Powerhouse.exe`:

```batch
BUILD_PRODUCTION.bat
```

**Output**: `electron-app/dist/Powerhouse Setup 1.0.0.exe`

This creates:
- ✅ **Setup.exe** - Professional Windows installer (~500-800 MB)
- ✅ **Powerhouse.exe** - Desktop launcher (after installation)
- ✅ Bundles all dependencies
- ✅ One-click installation for end users
- ✅ Native desktop app experience

See `BUILD_QUICK_REFERENCE.md` for quick guide or `electron-app/README_PRODUCTION.md` for detailed documentation.

### Docker

```bash
docker-compose up -d
```

### Production Server Deployment

See deployment guides in `backend/docs/` directory.

## 📝 License

[Your License Here]

## 🤝 Contributing

[Contributing guidelines]

## 📧 Support

[Support contact information]

---

## 📖 Additional Resources

- **Quick Start Guide**: See `QUICK_START.md` for step-by-step instructions
- **Installation Troubleshooting**: See `QUICK_START.md` (Troubleshooting section)
- **Architecture**: See `docs/ARCHITECTURE.md` for system design
- **Deployment**: See `docs/DEPLOYMENT_GUIDE.md` for production setup
- **Git Setup**: See `docs/GIT_SETUP.md` for repository configuration

---

**Note**: This is an active development project. For the fastest setup, use `INSTALL.bat` (one-click installer).

