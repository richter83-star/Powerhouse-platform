# Powerhouse Multi‑Agent System (19 roles)

FastAPI backend with 16 classic agents + 3 meta agents.

Run local:
  pip install -r requirements.txt
  uvicorn api.server:app --reload

Docker:
  docker build -t powerhouse-agents .
  docker run -p 8000:8000 powerhouse-agents

API:
POST /task  { "task": "string", "agents": [..], "config": {...} }
