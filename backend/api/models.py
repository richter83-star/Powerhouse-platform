"""
Pydantic models for API requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class WorkflowType(str, Enum):
    """Types of workflows available."""
    COMPLIANCE = "compliance"
    CUSTOMER_SUCCESS = "customer_success"
    CUSTOM = "custom"


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    """Status of an agent."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Request Models
# ============================================================================

class ComplianceWorkflowRequest(BaseModel):
    """Request model for compliance workflow."""
    
    query: str = Field(
        ...,
        description="The compliance query or policy text to analyze",
        min_length=10,
        max_length=10000
    )
    policy_documents: Optional[List[str]] = Field(
        default=None,
        description="Optional list of policy document URLs or paths"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Legal jurisdiction (e.g., 'US', 'EU', 'GDPR')"
    )
    risk_threshold: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Risk threshold for compliance evaluation (0-1)"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional configuration parameters"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Analyze our data retention policy for GDPR compliance",
                "jurisdiction": "EU",
                "risk_threshold": 0.8
            }
        }
    )


class WorkflowStatusRequest(BaseModel):
    """Request model for checking workflow status."""
    
    include_agent_details: bool = Field(
        default=False,
        description="Include detailed agent execution information"
    )


# ============================================================================
# Response Models
# ============================================================================

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


class AgentExecutionDetail(BaseModel):
    """Detailed information about an agent execution."""
    
    agent_name: str
    agent_type: str
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    
    workflow_id: str
    status: WorkflowStatus
    workflow_type: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    progress_percentage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Workflow completion percentage"
    )
    current_agent: Optional[str] = Field(
        default=None,
        description="Currently executing agent"
    )
    agent_executions: Optional[List[AgentExecutionDetail]] = Field(
        default=None,
        description="Detailed agent execution information"
    )
    error_message: Optional[str] = None


class ComplianceRiskAssessment(BaseModel):
    """Compliance risk assessment result."""
    
    risk_level: str = Field(..., description="Overall risk level (low/medium/high/critical)")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Numerical risk score (0-1)")
    findings: List[str] = Field(..., description="List of compliance findings")
    recommendations: List[str] = Field(..., description="List of recommendations")
    affected_regulations: List[str] = Field(
        default_factory=list,
        description="List of affected regulations"
    )


class ComplianceAnalysis(BaseModel):
    """Detailed compliance analysis."""
    
    summary: str = Field(..., description="Executive summary of the analysis")
    obligations: List[str] = Field(..., description="Identified compliance obligations")
    gaps: List[str] = Field(..., description="Identified compliance gaps")
    perspectives: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Multiple perspectives from debate agent"
    )
    evaluation_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall evaluation score"
    )


class ComplianceWorkflowResponse(BaseModel):
    """Response model for compliance workflow."""
    
    workflow_id: str
    status: WorkflowStatus
    message: str = Field(..., description="Status message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workflow_id": "wf_abc123",
                "status": "running",
                "message": "Compliance workflow started successfully"
            }
        }
    )


class ComplianceResultsResponse(BaseModel):
    """Response model for compliance workflow results."""
    
    workflow_id: str
    status: WorkflowStatus
    analysis: Optional[ComplianceAnalysis] = None
    risk_assessment: Optional[ComplianceRiskAssessment] = None
    compliance_report: Optional[str] = Field(
        default=None,
        description="Full compliance report in markdown format"
    )
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    
    agents: List[AgentInfo]
    total_count: int


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server timestamp")
    database_connected: bool = Field(..., description="Database connection status")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {"field": "query", "issue": "too short"},
                "timestamp": "2025-10-06T12:00:00Z"
            }
        }
    )


# ============================================================================
# Authentication Models
# ============================================================================

class Token(BaseModel):
    """JWT token response."""
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    
    username: Optional[str] = None
    tenant_id: Optional[str] = None


class User(BaseModel):
    """User model."""
    
    username: str
    email: Optional[str] = None
    tenant_id: str
    disabled: Optional[bool] = False
