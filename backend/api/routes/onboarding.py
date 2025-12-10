"""
Onboarding API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database.session import get_db
from api.auth import get_current_user
from database.models import User
from core.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class OnboardingCompleteRequest(BaseModel):
    use_case: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class OnboardingStatusResponse(BaseModel):
    started: bool
    completed: bool
    skipped: bool
    current_step: str
    progress_percentage: int
    completed_steps: list
    total_steps: int
    use_case: Optional[str] = None
    sample_workflow_created: bool = False
    sample_agent_created: bool = False
    first_run_completed: bool = False


class UpdateStepRequest(BaseModel):
    step_id: str
    completed: bool = True


@router.post("/complete")
async def complete_onboarding(
    request: OnboardingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark onboarding as complete for the current user.
    """
    try:
        onboarding_service = OnboardingService(db)
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        progress = onboarding_service.complete_onboarding(
            user_id=current_user.id,
            use_case=request.use_case,
            preferences=request.preferences
        )
        
        return {
            "message": "Onboarding completed successfully",
            "use_case": progress.use_case,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None
        }
    except Exception as e:
        logger.error(f"Complete onboarding error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )


@router.post("/skip")
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Skip onboarding for the current user.
    """
    try:
        onboarding_service = OnboardingService(db)
        progress = onboarding_service.skip_onboarding(current_user.id)
        
        return {
            "message": "Onboarding skipped",
            "skipped": progress.skipped
        }
    except Exception as e:
        logger.error(f"Skip onboarding error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip onboarding: {str(e)}"
        )


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get onboarding status for the current user.
    """
    try:
        onboarding_service = OnboardingService(db)
        summary = onboarding_service.get_progress_summary(current_user.id)
        
        return OnboardingStatusResponse(**summary)
    except Exception as e:
        logger.error(f"Get onboarding status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding status: {str(e)}"
        )


@router.post("/step")
async def update_step(
    request: UpdateStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update onboarding step progress.
    """
    try:
        onboarding_service = OnboardingService(db)
        progress = onboarding_service.update_step(
            user_id=current_user.id,
            step_id=request.step_id,
            completed=request.completed
        )
        
        return {
            "message": "Step updated successfully",
            "current_step": progress.current_step,
            "completed_steps": progress.completed_steps
        }
    except Exception as e:
        logger.error(f"Update step error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update step: {str(e)}"
        )


@router.post("/mark-sample-workflow")
async def mark_sample_workflow_created(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark that user has created a sample workflow."""
    try:
        onboarding_service = OnboardingService(db)
        progress = onboarding_service.mark_sample_workflow_created(current_user.id)
        
        return {
            "message": "Sample workflow marked as created",
            "sample_workflow_created": progress.sample_workflow_created
        }
    except Exception as e:
        logger.error(f"Mark sample workflow error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark sample workflow: {str(e)}"
        )


@router.post("/mark-sample-agent")
async def mark_sample_agent_created(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark that user has created a sample agent."""
    try:
        onboarding_service = OnboardingService(db)
        progress = onboarding_service.mark_sample_agent_created(current_user.id)
        
        return {
            "message": "Sample agent marked as created",
            "sample_agent_created": progress.sample_agent_created
        }
    except Exception as e:
        logger.error(f"Mark sample agent error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark sample agent: {str(e)}"
        )


@router.post("/mark-first-run")
async def mark_first_run_completed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark that user has completed their first workflow run."""
    try:
        onboarding_service = OnboardingService(db)
        progress = onboarding_service.mark_first_run_completed(current_user.id)
        
        return {
            "message": "First run marked as completed",
            "first_run_completed": progress.first_run_completed
        }
    except Exception as e:
        logger.error(f"Mark first run error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark first run: {str(e)}"
        )


@router.get("/sample-workflow")
async def get_sample_workflow(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sample workflow configuration for onboarding."""
    try:
        onboarding_service = OnboardingService(db)
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        sample_workflow = onboarding_service.create_sample_workflow(
            user_id=current_user.id,
            tenant_id=tenant_id
        )
        
        return sample_workflow
    except Exception as e:
        logger.error(f"Get sample workflow error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sample workflow: {str(e)}"
        )

