# Powerhouse Update Guide - Advanced Features

## Quick Answer: No Full Reinstall Needed! ✅

You **do NOT need to reinstall** Powerhouse. Just update dependencies and restart services.

## What Changed

✅ **New Python packages** added (for advanced AI features)
✅ **New backend code** added (10 advanced features modules)
✅ **New API routes** added
✅ **No database migrations** needed (advanced features use existing tables)
✅ **No frontend changes** needed

## Update Steps

### Option 1: Docker Setup (Recommended)

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild containers with new dependencies
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 3. Verify services are running
docker-compose ps
```

### Option 2: Local Development Setup

#### Backend Update:

```bash
cd backend

# 1. Pull latest code
git pull origin main

# 2. Update Python dependencies
pip install -r requirements.txt --upgrade

# 3. Restart backend service
# If using uvicorn directly:
pkill -f uvicorn
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

# Or if using your start script:
# Stop existing backend, then restart with your usual command
```

#### Frontend Update:

```bash
cd frontend/app

# 1. Pull latest code
git pull origin main

# 2. Install/update dependencies (if any changed)
npm install

# 3. Restart frontend (if running)
npm run dev
```

### Option 3: Using Batch Scripts (Windows)

```batch
# 1. Pull latest code
git pull origin main

# 2. Restart services (scripts will handle updates)
2_START_BACKEND.bat
3_START_FRONTEND.bat
```

## New Dependencies Installed

The following Python packages were added for advanced features:

- `networkx` - Graph structures for causal reasoning
- `pgmpy` - Causal inference
- `pandas` - Data handling
- `scipy` - Optimization algorithms
- `transformers` - Vision-language models
- `Pillow` - Image processing
- `openai-whisper` - Audio processing
- `restrictedpython` - Safe code execution
- `adversarial-robustness-toolbox` - Adversarial testing
- `torch-pruning` - Model compression

## Verification

After updating, verify the new features are available:

### 1. Check API Routes

Visit: `http://localhost:8001/docs`

You should see new endpoints under:
- `/api/advanced/causal/*` - Causal reasoning
- `/api/advanced/synthesis/*` - Program synthesis
- `/api/advanced/swarm/*` - Swarm intelligence
- `/api/advanced/multimodal/*` - Multi-modal learning
- etc.

### 2. Check Backend Logs

```bash
# Docker
docker-compose logs backend | grep -i "advanced"

# Local
# Check your backend logs for startup messages
```

You should see:
```
INFO - Advanced features routes loaded (causal reasoning, program synthesis, swarm, etc.)
```

### 3. Test Enhanced Agents

The enhanced agents are available but optional. They work with existing code.

## Configuration (Optional)

Advanced features are **disabled by default** to avoid impacting existing functionality.

To enable features, edit `backend/config/advanced_features_config.py` or set environment variables:

```bash
# Enable specific features
ADVANCED_FEATURES_ENABLE_CAUSAL_REASONING=true
ADVANCED_FEATURES_ENABLE_SWARM_INTELLIGENCE=true
ADVANCED_FEATURES_ENABLE_PROGRAM_SYNTHESIS=true
```

Or in code:
```python
from config.advanced_features_config import advanced_features_config

advanced_features_config.ENABLE_CAUSAL_REASONING = True
```

## Troubleshooting

### Issue: Import errors after update

**Solution**: Make sure all dependencies are installed:
```bash
cd backend
pip install -r requirements.txt --upgrade --force-reinstall
```

### Issue: Backend won't start

**Solution**: Check for missing dependencies:
```bash
cd backend
python -c "from core.reasoning import CausalReasoner; print('OK')"
```

### Issue: Tests failing

**Solution**: Tests may fail if dependencies aren't installed:
```bash
cd backend
pip install pytest pytest-cov
pytest tests/ -v
```

### Issue: Docker build fails

**Solution**: Clear Docker cache and rebuild:
```bash
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
```

## What If I Want a Fresh Install?

Only do this if you want to start completely fresh:

1. **Backup your data** (database, uploaded files, etc.)
2. **Stop all services**
3. **Remove old installation**
4. **Clone fresh repository**
5. **Follow original installation guide**

But this is **NOT necessary** - just updating is enough!

## Summary

✅ **No reinstall needed**
✅ **Just update dependencies**
✅ **Restart services**
✅ **Optional: Enable features via config**

The new features are **additive** and won't break existing functionality. They're ready to use when you enable them!

