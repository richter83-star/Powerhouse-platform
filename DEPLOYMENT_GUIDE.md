# Commercial-Grade System - Deployment Guide

## 🚀 Pre-Deployment Checklist

### ✅ System Requirements
- [ ] Python 3.12+ installed
- [ ] PostgreSQL database running (or SQLite for development)
- [ ] Redis server running (optional, for caching)
- [ ] Docker & Docker Compose (for database/Redis)
- [ ] Node.js 18+ (for frontend)
- [ ] All dependencies installed (`pip install -r requirements.txt`)

### ✅ Configuration
- [ ] Environment variables configured (`.env` file)
- [ ] Database connection string set
- [ ] JWT secret key generated
- [ ] Email service configured (SendGrid/AWS SES/SMTP)
- [ ] API keys configured (if using external services)

### ✅ Security
- [ ] All secrets in environment variables (not hardcoded)
- [ ] Database credentials secured
- [ ] HTTPS configured (for production)
- [ ] Firewall rules configured
- [ ] SSL certificates installed (for production)

### ✅ Testing
- [ ] All tests passing (100% pass rate confirmed)
- [ ] Database migrations tested
- [ ] Backup strategy in place

---

## 📋 Deployment Steps

### Step 1: Environment Setup

1. **Create `.env` file** (if not exists):
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/powerhouse
DB_HOST=localhost
DB_PORT=5432
DB_NAME=powerhouse
DB_USER=powerhouse_user
DB_PASSWORD=your_secure_password

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Service
EMAIL_PROVIDER=sendgrid  # or 'ses' or 'smtp'
SENDGRID_API_KEY=your-sendgrid-api-key
AWS_SES_REGION=us-east-1
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password
EMAIL_FROM=noreply@powerhouse.com

# Application
DEBUG=False
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 2: Database Initialization

```bash
# Initialize database tables
python -c "from database.session import init_db; init_db(drop_all=False)"
```

Or use the provided script:
```bash
python backend/scripts/init_database.py
```

### Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Run Database Migrations (if using Alembic)

```bash
cd backend
alembic upgrade head
```

### Step 5: Start Services

**Option A: Using Docker Compose (Recommended)**
```bash
docker-compose up -d
```

**Option B: Manual Start**
```bash
# Start backend
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd frontend
npm install
npm run build
npm start
```

### Step 6: Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Run test suite
python backend/scripts/test_commercial_grade.py
```

---

## 🔧 Production Deployment

### Using the Production Build Script

```bash
# Build production installer
BUILD_PRODUCTION.bat
```

This will create:
- `dist/setup.exe` - Windows installer
- `dist/Powerhouse.exe` - Application launcher

### Manual Production Setup

1. **Build Frontend**:
```bash
cd frontend
npm install
npm run build
```

2. **Build Backend** (if using PyInstaller):
```bash
cd backend
pyinstaller --onefile --name powerhouse_backend api/main.py
```

3. **Configure Production Settings**:
- Set `DEBUG=False`
- Configure production database
- Set up reverse proxy (nginx/Apache)
- Configure SSL certificates

---

## 📊 Post-Deployment Verification

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### 2. API Documentation
Visit: `http://localhost:8000/docs`

### 3. Test Critical Features
- [ ] License activation works
- [ ] Usage tracking works
- [ ] Email sending works
- [ ] Support tickets work
- [ ] Onboarding flow works

### 4. Monitor Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# Check for errors
grep ERROR backend/logs/app.log
```

---

## 🔄 Update/Upgrade Process

### 1. Backup Current Version
```bash
# Backup database
pg_dump powerhouse > backup_$(date +%Y%m%d).sql

# Backup configuration
cp .env .env.backup
```

### 2. Update Code
```bash
git pull origin main
```

### 3. Update Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### 4. Run Migrations
```bash
alembic upgrade head
```

### 5. Restart Services
```bash
# If using systemd
sudo systemctl restart powerhouse

# If using Docker
docker-compose restart
```

---

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check database is running
psql -U postgres -c "SELECT version();"

# Test connection
python -c "from database.session import get_engine; engine = get_engine(); print('Connected!')"
```

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <pid> /F
```

### Import Errors
```bash
# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📝 Deployment Checklist

- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Dependencies installed
- [ ] Services started
- [ ] Health check passing
- [ ] API documentation accessible
- [ ] Critical features tested
- [ ] Logs monitored
- [ ] Backup strategy in place
- [ ] Monitoring configured

---

## 🎯 Next Steps After Deployment

1. **Create Admin User**:
```bash
python backend/scripts/create_admin.py
```

2. **Configure License System**:
- Generate initial license keys
- Configure license tiers

3. **Set Up Monitoring**:
- Configure SLA monitoring
- Set up alerting

4. **Enable Features**:
- Configure email service
- Set up support system
- Enable onboarding flow

---

## 📞 Support

For deployment issues:
1. Check logs in `backend/logs/`
2. Review error messages
3. Verify environment variables
4. Check database connectivity
5. Review API documentation at `/docs`

---

**Status: ✅ System Ready for Deployment**

