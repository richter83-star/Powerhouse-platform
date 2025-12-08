"""
Workflow API routes.
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from api.models import (
    ComplianceWorkflowRequest,
    ComplianceWorkflowResponse,
    WorkflowStatusRequest,
    WorkflowStatusResponse,
    ComplianceResultsResponse,
    WorkflowStatus,
    AgentExecutionDetail
)
from api.auth import get_current_user
from api.models import User
from database.session import get_db
from database.models import Run, AgentRun, RunStatus
from workflows.compliance import ComplianceWorkflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post(
    "/compliance",
    response_model=ComplianceWorkflowResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start Compliance Workflow",
    description="Start a new compliance intelligence workflow for analyzing compliance queries"
)
async def start_compliance_workflow(
    request: ComplianceWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new compliance intelligence workflow.
    
    The workflow orchestrates multiple agents:
    1. Governor agent - Preflight compliance check
    2. ReAct agent - Analyzes the compliance query
    3. Debate agent - Generates multiple perspectives
    4. Evaluator agent - Assesses the analysis
    
    Returns immediately with workflow ID. Use the status endpoint to check progress.
    """
    try:
        # Initialize workflow
        workflow = ComplianceWorkflow(db_session=db)
        
        # Start workflow (creates database record)
        workflow_id = await workflow.start_workflow(
            query=request.query,
            tenant_id=current_user.tenant_id,
            config={
                "jurisdiction": request.jurisdiction,
                "risk_threshold": request.risk_threshold,
                "policy_documents": request.policy_documents,
                **(request.config or {})
            }
        )
        
        # Execute workflow in background
        background_tasks.add_task(
            workflow.execute_workflow,
            workflow_id,
            request.query,
            {
                "jurisdiction": request.jurisdiction,
                "risk_threshold": request.risk_threshold,
                "policy_documents": request.policy_documents,
                **(request.config or {})
            }
        )
        
        return ComplianceWorkflowResponse(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            message="Compliance workflow started successfully. Use the status endpoint to check progress."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start compliance workflow: {str(e)}"
        )


@router.get(
    "/{workflow_id}/status",
    response_model=WorkflowStatusResponse,
    summary="Get Workflow Status",
    description="Get the current status and progress of a workflow"
)
async def get_workflow_status(
    workflow_id: str,
    include_agent_details: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status and progress of a workflow.
    
    Returns current status, progress percentage, and optionally detailed
    information about each agent execution.
    """
    try:
        # Get run from database
        run = db.query(Run).filter(Run.id == workflow_id).first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Get agent runs
        agent_runs = db.query(AgentRun).filter(
            AgentRun.run_id == workflow_id
        ).order_by(AgentRun.created_at).all()
        
        # Calculate progress
        total_agents = 4  # react, debate, evaluator, governor
        completed_agents = sum(1 for ar in agent_runs if ar.status.value == "completed")
        progress = (completed_agents / total_agents) * 100 if total_agents > 0 else 0
        
        # Get current agent
        current_agent = None
        for ar in agent_runs:
            if ar.status.value == "running":
                current_agent = ar.agent_name
                break
        
        # Calculate duration
        duration = None
        if run.started_at:
            end_time = run.completed_at or None
            if end_time:
                duration = (end_time - run.started_at).total_seconds()
        
        # Build agent execution details if requested
        agent_executions = None
        if include_agent_details:
            agent_executions = []
            for ar in agent_runs:
                exec_duration = None
                if ar.started_at and ar.completed_at:
                    exec_duration = (ar.completed_at - ar.started_at).total_seconds()
                
                agent_executions.append(
                    AgentExecutionDetail(
                        agent_name=ar.agent_name,
                        agent_type=ar.agent_type,
                        status=ar.status.value,
                        input_data=ar.input_data,
                        output_data=ar.output_data,
                        error_message=ar.error_message,
                        metrics=ar.metrics,
                        started_at=ar.started_at,
                        completed_at=ar.completed_at,
                        duration_seconds=exec_duration
                    )
                )
        
        return WorkflowStatusResponse(
            workflow_id=run.id,
            status=WorkflowStatus(run.status.value),
            workflow_type="compliance",
            created_at=run.created_at,
            updated_at=run.updated_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_seconds=duration,
            progress_percentage=progress,
            current_agent=current_agent,
            agent_executions=agent_executions,
            error_message=run.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get(
    "/{workflow_id}/results",
    response_model=ComplianceResultsResponse,
    summary="Get Workflow Results",
    description="Get the final results of a completed workflow"
)
async def get_workflow_results(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the final results of a completed workflow.
    
    Returns the complete compliance analysis, risk assessment, and report.
    Only available for completed workflows.
    """
    try:
        # Get run from database
        run = db.query(Run).filter(Run.id == workflow_id).first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Check if workflow is completed
        if run.status != RunStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow is not completed yet. Current status: {run.status.value}"
            )
        
        # Calculate duration
        duration = None
        if run.started_at and run.completed_at:
            duration = (run.completed_at - run.started_at).total_seconds()
        
        # Extract results
        output_data = run.output_data or {}
        
        return ComplianceResultsResponse(
            workflow_id=run.id,
            status=WorkflowStatus(run.status.value),
            analysis=output_data.get("analysis"),
            risk_assessment=output_data.get("risk_assessment"),
            compliance_report=output_data.get("compliance_report"),
            created_at=run.created_at,
            completed_at=run.completed_at,
            duration_seconds=duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow results: {str(e)}"
        )
