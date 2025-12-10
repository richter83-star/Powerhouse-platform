# Powerhouse Multi-Agent Platform

Enterprise-grade multi-agent AI platform for B2B use cases. Orchestrates 19+ specialized AI agents to solve complex business challenges.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with multi-agent orchestrator
- **Frontend**: Next.js 14 (React 18, TypeScript)
- **Database**: PostgreSQL 15
- **Desktop**: Electron wrapper for standalone deployment
- **Infrastructure**: Docker Compose for containerization

## 🚀 Quick Start

### Prerequisites

Before installing, make sure you have:

- **Python 3.11+** - [Download](https://www.python.org/downloads/) (check "Add Python to PATH")
- **Node.js 18+** - [Download](https://nodejs.org/) (LTS version recommended)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/) (for database)
- **Git** (optional, for cloning the repository)

### One-Click Installation (Recommended)

**Windows Users - Just 2 Steps:**

1. **Double-click `INSTALL.bat`**
   - ✅ Checks all prerequisites automatically
   - ✅ Installs backend dependencies (Python packages)
   - ✅ Installs frontend dependencies (Node.js packages)
   - ✅ Sets up environment files
   - ✅ Verifies installation
   - ⏱️ Takes 5-10 minutes

2. **Double-click `START_POWERHOUSE_FULL.bat`**
   - ✅ Starts PostgreSQL database
   - ✅ Starts FastAPI backend (port 8001)
   - ✅ Starts Next.js frontend (port 3000)
   - ✅ Opens browser automatically
   - ⏱️ Takes 30-60 seconds

**That's it!** You're ready to use Powerhouse at http://localhost:3000

> 💡 **Tip:** See `QUICK_START.md` for detailed step-by-step instructions and troubleshooting.

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
venv\Scripts\activate  # Windows (activate virtual environment)
# Or: source venv/bin/activate  # Linux/Mac

# Install dependencies (if not already done)
pip install -r requirements.txt

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
pytest tests/ -v

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

