"""
Onboarding Service

Manages user onboarding progress, sample data creation, and tutorial tracking.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import OnboardingProgress, User, Tenant, Project, Run
from database.session import get_db

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service for managing user onboarding.
    
    Features:
    - Progress tracking
    - Step completion
    - Sample data creation
    - Tutorial management
    """
    
    # Onboarding steps
    STEPS = [
        {"id": "welcome", "name": "Welcome", "order": 0},
        {"id": "use-case", "name": "Use Case Selection", "order": 1},
        {"id": "tour", "name": "Platform Tour", "order": 2},
        {"id": "sample-workflow", "name": "Create Sample Workflow", "order": 3},
        {"id": "sample-agent", "name": "Create Sample Agent", "order": 4},
        {"id": "first-run", "name": "Run First Workflow", "order": 5},
        {"id": "complete", "name": "Complete", "order": 6}
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_progress(self, user_id: str, tenant_id: Optional[str] = None) -> OnboardingProgress:
        """Get or create onboarding progress for user."""
        progress = self.db.query(OnboardingProgress).filter(
            OnboardingProgress.user_id == user_id
        ).first()
        
        if not progress:
            progress = OnboardingProgress(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                current_step="welcome",
                completed_steps=[],
                skipped=False,
                started_at=datetime.utcnow()
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)
        
        return progress
    
    def update_step(self, user_id: str, step_id: str, completed: bool = True) -> OnboardingProgress:
        """Update onboarding step progress."""
        progress = self.get_or_create_progress(user_id)
        
        if completed and step_id not in progress.completed_steps:
            progress.completed_steps.append(step_id)
        
        progress.current_step = step_id
        progress.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def complete_onboarding(
        self,
        user_id: str,
        use_case: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> OnboardingProgress:
        """Mark onboarding as complete."""
        progress = self.get_or_create_progress(user_id)
        
        progress.current_step = "complete"
        progress.completed_steps.append("complete")
        progress.completed_at = datetime.utcnow()
        progress.use_case = use_case
        if preferences:
            progress.preferences.update(preferences)
        
        self.db.commit()
        self.db.refresh(progress)
        
        logger.info(f"Onboarding completed for user {user_id}")
        return progress
    
    def skip_onboarding(self, user_id: str) -> OnboardingProgress:
        """Skip onboarding for user."""
        progress = self.get_or_create_progress(user_id)
        progress.skipped = True
        progress.completed_at = datetime.utcnow()
        progress.current_step = "complete"
        
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def get_progress(self, user_id: str) -> Optional[OnboardingProgress]:
        """Get onboarding progress for user."""
        return self.db.query(OnboardingProgress).filter(
            OnboardingProgress.user_id == user_id
        ).first()
    
    def mark_sample_workflow_created(self, user_id: str) -> OnboardingProgress:
        """Mark that user has created a sample workflow."""
        progress = self.get_or_create_progress(user_id)
        progress.sample_workflow_created = True
        progress.completed_steps.append("sample-workflow")
        progress.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def mark_sample_agent_created(self, user_id: str) -> OnboardingProgress:
        """Mark that user has created a sample agent."""
        progress = self.get_or_create_progress(user_id)
        progress.sample_agent_created = True
        progress.completed_steps.append("sample-agent")
        progress.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def mark_first_run_completed(self, user_id: str) -> OnboardingProgress:
        """Mark that user has completed their first workflow run."""
        progress = self.get_or_create_progress(user_id)
        progress.first_run_completed = True
        progress.completed_steps.append("first-run")
        progress.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def create_sample_workflow(self, user_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a sample workflow for onboarding.
        
        Returns workflow configuration that can be used to create a workflow.
        """
        sample_workflow = {
            "name": "Sample Compliance Workflow",
            "description": "A sample workflow to help you get started with Powerhouse",
            "agents": [
                {
                    "agent_id": "researcher",
                    "config": {
                        "task": "Research compliance requirements for a new product launch"
                    }
                },
                {
                    "agent_id": "analyst",
                    "config": {
                        "task": "Analyze research findings and identify key compliance areas"
                    }
                }
            ],
            "metadata": {
                "onboarding": True,
                "sample": True
            }
        }
        
        return sample_workflow
    
    def get_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """Get onboarding progress summary."""
        progress = self.get_progress(user_id)
        
        if not progress:
            return {
                "started": False,
                "completed": False,
                "skipped": False,
                "current_step": "welcome",
                "progress_percentage": 0,
                "completed_steps": [],
                "total_steps": len(self.STEPS)
            }
        
        completed_count = len(progress.completed_steps)
        total_steps = len(self.STEPS)
        progress_percentage = int((completed_count / total_steps) * 100) if total_steps > 0 else 0
        
        return {
            "started": True,
            "completed": progress.completed_at is not None,
            "skipped": progress.skipped,
            "current_step": progress.current_step,
            "progress_percentage": progress_percentage,
            "completed_steps": progress.completed_steps,
            "total_steps": total_steps,
            "use_case": progress.use_case,
            "sample_workflow_created": progress.sample_workflow_created,
            "sample_agent_created": progress.sample_agent_created,
            "first_run_completed": progress.first_run_completed
        }

