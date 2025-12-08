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

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15 (or use Docker)

### Installation

1. **Run Diagnostics** (recommended first step):
   ```bash
   DIAGNOSE.bat
   ```

2. **Install Dependencies**:
   ```bash
   INSTALL_FIXED_V2.bat
   ```

3. **Start Services**:
   ```bash
   START_POWERHOUSE_FULL.bat
   ```
   
   Or start individually:
   ```bash
   1_START_DATABASE.bat    # PostgreSQL
   2_START_BACKEND.bat     # FastAPI (port 8001)
   3_START_FRONTEND.bat    # Next.js (port 3000)
   ```

4. **Access Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

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

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn api.server:app --reload
```

### Frontend

```bash
cd frontend/app
npm install
npm run dev
```

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

### Docker

```bash
docker-compose up -d
```

### Production

See deployment guides in `backend/docs/` directory.

## 📝 License

[Your License Here]

## 🤝 Contributing

[Contributing guidelines]

## 📧 Support

[Support contact information]

---

**Note**: This is an active development project. See `README_FIRST.txt` for installation troubleshooting.

