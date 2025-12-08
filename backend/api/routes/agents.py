"""
Agent API routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from api.models import AgentInfo, AgentListResponse, AgentStatus
from api.auth import get_current_user, get_optional_user
from api.models import User

router = APIRouter(prefix="/agents", tags=["agents"])


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


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List Available Agents",
    description="Get a list of all available agents in the platform"
)
async def list_agents(
    current_user: User = Depends(get_optional_user)
):
    """
    List all available agents in the multi-agent platform.
    
    Returns information about each agent including its capabilities,
    type, and current status.
    """
    try:
        agents = []
        
        for agent_id, metadata in AGENT_METADATA.items():
            agents.append(
                AgentInfo(
                    id=agent_id,
                    name=metadata["name"],
                    type=metadata["type"],
                    description=metadata["description"],
                    status=AgentStatus.IDLE,  # In production, check actual status
                    capabilities=metadata["capabilities"]
                )
            )
        
        return AgentListResponse(
            agents=agents,
            total_count=len(agents)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@router.get(
    "/{agent_id}/status",
    response_model=AgentInfo,
    summary="Get Agent Status",
    description="Get detailed status information for a specific agent"
)
async def get_agent_status(
    agent_id: str,
    current_user: User = Depends(get_optional_user)
):
    """
    Get detailed status information for a specific agent.
    
    Returns the agent's current status, capabilities, and metadata.
    """
    try:
        # Check if agent exists
        if agent_id not in AGENT_METADATA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found"
            )
        
        metadata = AGENT_METADATA[agent_id]
        
        return AgentInfo(
            id=agent_id,
            name=metadata["name"],
            type=metadata["type"],
            description=metadata["description"],
            status=AgentStatus.IDLE,  # In production, check actual status
            capabilities=metadata["capabilities"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )
