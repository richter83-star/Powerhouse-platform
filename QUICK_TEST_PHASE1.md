# Quick Phase 1 Test Guide

## Quick Start Testing

### 1. Start Services
```bash
# Terminal 1: Start Backend
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start Frontend
cd frontend/app
npm run dev
```

### 2. Run Automated Tests
```bash
# Windows
TEST_PHASE1.bat

# Or manually
python backend/scripts/test_phase1.py
```

### 3. Manual UI Testing

#### License Management
1. Open browser: `http://localhost:3000/settings/license`
2. Test license activation
3. Verify hardware fingerprint shows

#### Usage Dashboard
1. Open: `http://localhost:3000/billing/usage`
2. Check usage metrics
3. Verify projections

#### Support System
1. Open: `http://localhost:3000/support`
2. Create a test ticket
3. Test chat widget (bottom-right button)

### 4. API Testing

#### Test License API
```bash
# Get hardware fingerprint
curl http://localhost:8001/api/v1/license/hardware-fingerprint

# Validate license (no auth needed)
curl -X POST http://localhost:8001/api/v1/license/validate \
  -H "Content-Type: application/json" \
  -d '{"license_key": "TEST-XXXX-XXXX-XXXX-XXXX"}'
```

#### Test Usage API
```bash
# Get current usage (requires auth token)
curl http://localhost:8001/api/v1/usage/current-month \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get usage status
curl http://localhost:8001/api/v1/usage/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Test Support API
```bash
# Create ticket (requires auth token)
curl -X POST http://localhost:8001/api/v1/support/tickets \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Ticket",
    "description": "Testing support system",
    "priority": "medium"
  }'
```

## Expected Results

✅ **License System**: Keys generate, activate, validate correctly
✅ **Usage Tracking**: Metrics display, limits enforce, projections work
✅ **Email System**: Templates render, queue processes
✅ **Support System**: Tickets create, messages thread, chat works

## Troubleshooting

**Database tables not created?**
- Check backend logs for errors
- Run: `python -c "from database.session import init_db; init_db()"`

**API returns 404?**
- Verify routes are registered in `api/main.py`
- Check backend is running on port 8001

**Frontend not loading?**
- Check frontend is running on port 3000
- Verify API URL in frontend `.env`

## Next Steps

After successful testing:
1. Document any issues
2. Fix critical bugs
3. Proceed to Phase 2

