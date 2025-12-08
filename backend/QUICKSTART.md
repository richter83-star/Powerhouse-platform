# Quick Start Guide

Get the Powerhouse B2B Platform running in 5 minutes!

## Prerequisites

- Python 3.9+
- pip

## Installation

```bash
# 1. Navigate to backend directory
cd /home/ubuntu/powerhouse_b2b_platform/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
```

## Configuration

Edit `.env` and add your API key:

```bash
# For OpenAI
APP_OPENAI_API_KEY=sk-your-key-here

# OR for Anthropic
APP_ANTHROPIC_API_KEY=your-key-here
```

## Run Demo

```bash
python main.py
```

You should see:
- Database initialization
- Agent loading (react, evaluator)
- Task execution
- Results and statistics

## What Just Happened?

1. **Database Created**: SQLite database with all tables
2. **Agents Loaded**: React and Evaluator agents dynamically loaded
3. **Communication Established**: Agents registered with protocol
4. **Task Executed**: Multi-agent analysis performed
5. **Results Logged**: All communication persisted to database

## Next Steps

### Add More Agents

Edit `.env`:
```bash
APP_ENABLED_AGENTS=["react","evaluator","planning","memory_agent"]
```

### Use Different LLM

```bash
# Switch to Claude
APP_ANTHROPIC_API_KEY=your-key
APP_ANTHROPIC_DEFAULT_MODEL=claude-3-opus-20240229
```

### Create Custom Agent

Create `agents/my_agent.py`:

```python
from typing import Dict, Any
from core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    CAPABILITIES = ["custom_capability"]
    
    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Your logic here
        return {
            "status": "success",
            "output": {"result": "Hello from my agent!"},
            "metadata": {}
        }
```

Add to `.env`:
```bash
APP_ENABLED_AGENTS=["react","evaluator","my_agent"]
```

Run again - your agent is automatically discovered!

## Explore the Code

- **Communication Protocol**: `communication/` - The heart of the system
- **Agent Base Class**: `core/base_agent.py` - What all agents inherit
- **Orchestrator**: `core/orchestrator.py` - Manages execution
- **Example Agents**: `agents/react.py`, `agents/evaluator.py`

## Common Issues

### "No module named 'X'"
```bash
pip install -r requirements.txt
```

### "API key not found"
Make sure `.env` file exists and has your API key.

### "Database locked"
Delete `powerhouse.db` and run again.

## Documentation

- **README.md**: Full documentation
- **ARCHITECTURE.md**: System architecture
- **COMMUNICATION_PROTOCOL.md**: Deep dive into agent communication

## Support

Questions? Check the documentation or contact support.

---

**You're ready to build enterprise multi-agent systems! 🚀**
