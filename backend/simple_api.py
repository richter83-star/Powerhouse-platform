
"""
Simplified FastAPI backend for testing the agents endpoint.
This version has minimal dependencies and is easy to debug.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from enum import Enum

app = FastAPI(title="Powerhouse API - Simplified")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentStatus(str, Enum):
    """Status of an agent."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentInfo(BaseModel):
    """Information about an agent."""
    
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    description: str = Field(..., description="Agent description")
    status: AgentStatus = Field(..., description="Current agent status")
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of agent capabilities"
    )


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    
    agents: List[AgentInfo]
    total_count: int


# Agent metadata
AGENT_METADATA = {
    "react": {
        "name": "react",
        "type": "ReActAgent",
        "description": "Reasoning and Acting agent that analyzes compliance queries using structured reasoning",
        "capabilities": [
            "Structured reasoning",
            "Action planning",
            "Compliance analysis",
            "Policy interpretation"
        ]
    },
    "debate": {
        "name": "debate",
        "type": "DebateAgent",
        "description": "Multi-perspective debate agent that generates diverse viewpoints on compliance issues",
        "capabilities": [
            "Multiple perspective generation",
            "Argument synthesis",
            "Risk scenario analysis",
            "Stakeholder viewpoint modeling"
        ]
    },
    "evaluator": {
        "name": "evaluator",
        "type": "EvaluatorAgent",
        "description": "Evaluation agent that assesses compliance analysis quality and risk levels",
        "capabilities": [
            "Quality assessment",
            "Risk scoring",
            "Compliance evaluation",
            "Confidence measurement"
        ]
    },
    "governor": {
        "name": "governor",
        "type": "GovernorAgent",
        "description": "Governance agent that performs preflight checks and ensures policy compliance",
        "capabilities": [
            "Content filtering",
            "Policy enforcement",
            "Preflight validation",
            "Safety checks"
        ]
    },
    "planning": {
        "name": "planning",
        "type": "PlanningAgent",
        "description": "Strategic planning agent for complex multi-step compliance workflows",
        "capabilities": [
            "Strategic planning",
            "Task decomposition",
            "Workflow optimization",
            "Resource allocation"
        ]
    },
    "memory": {
        "name": "memory",
        "type": "MemoryAgent",
        "description": "Memory management agent for context retention and retrieval",
        "capabilities": [
            "Context storage",
            "Information retrieval",
            "Knowledge management",
            "Historical analysis"
        ]
    },
    "reflection": {
        "name": "reflection",
        "type": "ReflectionAgent",
        "description": "Self-reflection agent that improves analysis through iterative refinement",
        "capabilities": [
            "Self-assessment",
            "Iterative improvement",
            "Quality refinement",
            "Error correction"
        ]
    },
    "tree_of_thought": {
        "name": "tree_of_thought",
        "type": "TreeOfThoughtAgent",
        "description": "Tree-of-thought reasoning agent for exploring multiple solution paths",
        "capabilities": [
            "Branching reasoning",
            "Path exploration",
            "Solution comparison",
            "Decision tree analysis"
        ]
    },
    "chain_of_thought": {
        "name": "chain_of_thought",
        "type": "ChainOfThoughtAgent",
        "description": "Chain-of-thought reasoning agent for step-by-step logical analysis",
        "capabilities": [
            "Sequential reasoning",
            "Step-by-step analysis",
            "Logical deduction",
            "Transparent thinking"
        ]
    },
    "multi_agent": {
        "name": "multi_agent",
        "type": "MultiAgent",
        "description": "Multi-agent coordinator for parallel task execution",
        "capabilities": [
            "Parallel execution",
            "Agent coordination",
            "Task distribution",
            "Result aggregation"
        ]
    },
    "swarm": {
        "name": "swarm",
        "type": "SwarmAgent",
        "description": "Swarm intelligence agent for collective problem-solving",
        "capabilities": [
            "Collective intelligence",
            "Distributed processing",
            "Consensus building",
            "Emergent behavior"
        ]
    },
    "hierarchical": {
        "name": "hierarchical",
        "type": "HierarchicalAgent",
        "description": "Hierarchical agent system for structured task delegation",
        "capabilities": [
            "Hierarchical planning",
            "Task delegation",
            "Supervision",
            "Structured coordination"
        ]
    },
    "curriculum": {
        "name": "curriculum",
        "type": "CurriculumAgent",
        "description": "Curriculum learning agent that adapts to increasing complexity",
        "capabilities": [
            "Progressive learning",
            "Difficulty adaptation",
            "Skill building",
            "Incremental improvement"
        ]
    },
    "meta_evolver": {
        "name": "meta_evolver",
        "type": "MetaEvolverAgent",
        "description": "Meta-learning agent that evolves strategies over time",
        "capabilities": [
            "Strategy evolution",
            "Meta-learning",
            "Adaptive optimization",
            "Performance improvement"
        ]
    },
    "toolformer": {
        "name": "toolformer",
        "type": "ToolformerAgent",
        "description": "Tool-using agent that leverages external tools and APIs",
        "capabilities": [
            "Tool selection",
            "API integration",
            "External resource usage",
            "Function calling"
        ]
    },
    "voyager": {
        "name": "voyager",
        "type": "VoyagerAgent",
        "description": "Exploration agent for discovering new solutions and approaches",
        "capabilities": [
            "Exploration",
            "Discovery",
            "Innovation",
            "Novel solution generation"
        ]
    },
    "generative": {
        "name": "generative",
        "type": "GenerativeAgent",
        "description": "Generative agent for creating synthetic data and scenarios",
        "capabilities": [
            "Content generation",
            "Scenario creation",
            "Synthetic data",
            "Creative synthesis"
        ]
    },
    "adaptive_memory": {
        "name": "adaptive_memory",
        "type": "AdaptiveMemoryAgent",
        "description": "Adaptive memory agent with dynamic context management",
        "capabilities": [
            "Dynamic memory",
            "Context adaptation",
            "Intelligent caching",
            "Priority management"
        ]
    },
    "auto_loop": {
        "name": "auto_loop",
        "type": "AutoLoopAgent",
        "description": "Autonomous loop agent for self-directed task execution",
        "capabilities": [
            "Autonomous operation",
            "Self-direction",
            "Loop management",
            "Continuous improvement"
        ]
    }
}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Powerhouse Multi-Agent Platform API",
        "version": "1.0.0-simple",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "agents": "/api/v1/agents"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0-simple"}


@app.get("/api/v1/agents", response_model=AgentListResponse)
async def list_agents():
    """List all available agents."""
    try:
        agents = []
        
        for agent_id, metadata in AGENT_METADATA.items():
            agents.append(
                AgentInfo(
                    id=agent_id,
                    name=metadata["name"],
                    type=metadata["type"],
                    description=metadata["description"],
                    status=AgentStatus.IDLE,
                    capabilities=metadata["capabilities"]
                )
            )
        
        return AgentListResponse(
            agents=agents,
            total_count=len(agents)
        )
        
    except Exception as e:
        return AgentListResponse(agents=[], total_count=0)


@app.get("/api/v1/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """Get information about a specific agent."""
    if agent_id not in AGENT_METADATA:
        return {"detail": f"Agent '{agent_id}' not found"}
    
    metadata = AGENT_METADATA[agent_id]
    
    return AgentInfo(
        id=agent_id,
        name=metadata["name"],
        type=metadata["type"],
        description=metadata["description"],
        status=AgentStatus.IDLE,
        capabilities=metadata["capabilities"]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
