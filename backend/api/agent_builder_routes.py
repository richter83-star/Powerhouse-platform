
"""
Agent Builder API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

router = APIRouter()

class AgentConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    description: str
    agent_type: str
    capabilities: List[str]
    tools: List[str]
    memory_enabled: bool = False
    multi_step: bool = False
    custom_logic: Optional[str] = None
    api_integrations: List[str] = []
    learning_capability: bool = False
    reasoning_depth: int = 1
    collaboration: bool = False

class AgentPricing(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    complexity_score: int
    tier_name: str
    suggested_price: float
    min_price: float
    max_price: float

class CustomAgent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    description: str
    agent_type: str
    config: Dict[str, Any]
    complexity_score: int
    estimated_cost: float
    is_public: bool
    created_at: datetime

# Mock storage
custom_agents_db = []

def calculate_complexity_score(config: AgentConfig) -> int:
    """Calculate complexity score based on agent configuration"""
    from ..config.marketplace_config import COMPLEXITY_FACTORS
    
    score = 0
    
    # Base complexity
    score += len(config.tools) * COMPLEXITY_FACTORS["num_tools"]
    
    # Feature complexity
    if config.memory_enabled:
        score += COMPLEXITY_FACTORS["memory_enabled"]
    if config.multi_step:
        score += COMPLEXITY_FACTORS["multi_step"]
    if config.custom_logic:
        score += COMPLEXITY_FACTORS["custom_logic"]
    if config.api_integrations:
        score += len(config.api_integrations) * COMPLEXITY_FACTORS["api_integrations"]
    if config.learning_capability:
        score += COMPLEXITY_FACTORS["learning_capability"]
    if config.collaboration:
        score += COMPLEXITY_FACTORS["collaboration"]
    
    # Reasoning depth
    score += config.reasoning_depth * COMPLEXITY_FACTORS["reasoning_depth"]
    
    # Convert to 1-10 scale
    normalized_score = min(10, max(1, int(score / 20) + 1))
    return normalized_score

def get_pricing_for_complexity(complexity: int) -> Dict[str, Any]:
    """Get pricing information for a complexity score"""
    from ..config.marketplace_config import AGENT_PRICING_TIERS
    
    tier = AGENT_PRICING_TIERS.get(complexity, AGENT_PRICING_TIERS[1])
    suggested_price = (tier["min"] + tier["max"]) / 2
    
    return {
        "complexity_score": complexity,
        "tier_name": tier["name"],
        "suggested_price": suggested_price,
        "min_price": tier["min"],
        "max_price": tier["max"]
    }

@router.post("/agent-builder/calculate-pricing")
async def calculate_agent_pricing(config: AgentConfig):
    """Calculate pricing based on agent complexity"""
    complexity = calculate_complexity_score(config)
    pricing = get_pricing_for_complexity(complexity)
    
    return {
        "pricing": pricing,
        "breakdown": {
            "tools": len(config.tools),
            "memory": config.memory_enabled,
            "multi_step": config.multi_step,
            "custom_logic": bool(config.custom_logic),
            "api_integrations": len(config.api_integrations),
            "learning": config.learning_capability,
            "reasoning_depth": config.reasoning_depth,
            "collaboration": config.collaboration
        }
    }

@router.post("/agent-builder/create")
async def create_custom_agent(config: AgentConfig):
    """Create a custom agent"""
    complexity = calculate_complexity_score(config)
    pricing = get_pricing_for_complexity(complexity)
    
    agent = {
        "id": len(custom_agents_db) + 1,
        "user_id": 1,  # Get from auth
        "name": config.name,
        "description": config.description,
        "agent_type": config.agent_type,
        "config": config.model_dump(),
        "complexity_score": complexity,
        "estimated_cost": pricing["suggested_price"],
        "is_public": False,
        "created_at": datetime.now().isoformat()
    }
    
    custom_agents_db.append(agent)
    
    return {
        "agent": agent,
        "pricing": pricing,
        "message": "Custom agent created successfully"
    }

@router.get("/agent-builder/my-agents")
async def get_my_agents():
    """Get user's custom agents"""
    # Filter by authenticated user
    user_agents = [a for a in custom_agents_db if a["user_id"] == 1]
    return {"agents": user_agents}

@router.get("/agent-builder/agent/{agent_id}")
async def get_agent(agent_id: int):
    """Get agent details"""
    agent = next((a for a in custom_agents_db if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/agent-builder/agent/{agent_id}")
async def update_agent(agent_id: int, config: AgentConfig):
    """Update custom agent"""
    agent = next((a for a in custom_agents_db if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Recalculate complexity and pricing
    complexity = calculate_complexity_score(config)
    pricing = get_pricing_for_complexity(complexity)
    
    agent.update({
        "name": config.name,
        "description": config.description,
        "agent_type": config.agent_type,
        "config": config.model_dump(),
        "complexity_score": complexity,
        "estimated_cost": pricing["suggested_price"]
    })
    
    return {"agent": agent, "message": "Agent updated successfully"}

@router.delete("/agent-builder/agent/{agent_id}")
async def delete_agent(agent_id: int):
    """Delete custom agent"""
    global custom_agents_db
    custom_agents_db = [a for a in custom_agents_db if a["id"] != agent_id]
    return {"message": "Agent deleted successfully"}

@router.get("/agent-builder/templates")
async def get_agent_templates():
    """Get pre-built agent templates"""
    templates = [
        {
            "id": 1,
            "name": "Customer Support Bot",
            "description": "Intelligent customer support agent with memory and context",
            "agent_type": "chatbot",
            "capabilities": ["conversation", "memory", "escalation"],
            "complexity": 5,
            "suggested_price": 87.50
        },
        {
            "id": 2,
            "name": "Data Analytics Agent",
            "description": "Analyze data and generate insights",
            "agent_type": "analytics",
            "capabilities": ["data_analysis", "visualization", "reporting"],
            "complexity": 7,
            "suggested_price": 200.00
        },
        {
            "id": 3,
            "name": "Content Creator",
            "description": "Generate creative content with AI",
            "agent_type": "creative",
            "capabilities": ["writing", "image_gen", "multi_modal"],
            "complexity": 6,
            "suggested_price": 125.00
        }
    ]
    return {"templates": templates}
