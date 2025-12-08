"""
Onboarding API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.session import get_db
from core.security import get_current_user
from database.models import User

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class OnboardingCompleteRequest(BaseModel):
    use_case: str | None = None


class OnboardingStatusResponse(BaseModel):
    completed: bool
    use_case: str | None = None


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
        # In a real implementation, you might store this in a user preferences table
        # For now, we'll just return success
        # You could add: user.onboarding_completed = True, user.use_case = request.use_case
        
        return {
            "message": "Onboarding completed successfully",
            "use_case": request.use_case
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )


@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get onboarding status for the current user.
    """
    # In a real implementation, check user.onboarding_completed
    # For now, return not completed
    return OnboardingStatusResponse(
        completed=False,
        use_case=None
    )

