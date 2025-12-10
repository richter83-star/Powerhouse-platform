"""
Support API Routes

Handles support tickets, messages, and customer support operations.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from database.session import get_db
from database.models import User
from api.auth import get_current_user
from core.services.support_service import (
    SupportService,
    TicketStatus,
    TicketPriority,
    SupportTicket,
    SupportMessage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/support", tags=["Support"])

# Request/Response Models
class CreateTicketRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority: str = Field(default="medium")
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class AddMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    is_internal: bool = Field(default=False)


class UpdateTicketRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None


class TicketResponse(BaseModel):
    id: str
    user_id: str
    tenant_id: Optional[str]
    subject: str
    description: str
    status: str
    priority: str
    category: Optional[str]
    tags: List[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    assigned_to: Optional[str]


class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    user_id: str
    message: str
    is_internal: bool
    created_at: str


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    request: CreateTicketRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new support ticket."""
    try:
        support_service = SupportService(db)
        
        priority = TicketPriority(request.priority.lower()) if request.priority else TicketPriority.MEDIUM
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        ticket = support_service.create_ticket(
            user_id=current_user.id,
            subject=request.subject,
            description=request.description,
            tenant_id=tenant_id,
            priority=priority,
            category=request.category,
            tags=request.tags
        )
        
        return TicketResponse(
            id=ticket.id,
            user_id=ticket.user_id,
            tenant_id=ticket.tenant_id,
            subject=ticket.subject,
            description=ticket.description,
            status=ticket.status.value,
            priority=ticket.priority.value,
            category=ticket.category,
            tags=ticket.tags,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat(),
            resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            assigned_to=ticket.assigned_to
        )
    except Exception as e:
        logger.error(f"Create ticket error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support ticket"
        )


@router.get("/tickets", response_model=List[TicketResponse])
async def get_my_tickets(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tickets for current user."""
    try:
        support_service = SupportService(db)
        
        status_enum = TicketStatus(status_filter.lower()) if status_filter else None
        
        tickets = support_service.get_user_tickets(
            user_id=current_user.id,
            status=status_enum
        )
        
        return [
            TicketResponse(
                id=t.id,
                user_id=t.user_id,
                tenant_id=t.tenant_id,
                subject=t.subject,
                description=t.description,
                status=t.status.value,
                priority=t.priority.value,
                category=t.category,
                tags=t.tags,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
                resolved_at=t.resolved_at.isoformat() if t.resolved_at else None,
                assigned_to=t.assigned_to
            )
            for t in tickets
        ]
    except Exception as e:
        logger.error(f"Get tickets error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tickets"
        )


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific ticket."""
    try:
        support_service = SupportService(db)
        
        ticket = support_service.get_ticket(ticket_id, user_id=current_user.id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        return TicketResponse(
            id=ticket.id,
            user_id=ticket.user_id,
            tenant_id=ticket.tenant_id,
            subject=ticket.subject,
            description=ticket.description,
            status=ticket.status.value,
            priority=ticket.priority.value,
            category=ticket.category,
            tags=ticket.tags,
            created_at=ticket.created_at.isoformat(),
            updated_at=ticket.updated_at.isoformat(),
            resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            assigned_to=ticket.assigned_to
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ticket error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ticket"
        )


@router.post("/tickets/{ticket_id}/messages", response_model=MessageResponse)
async def add_message(
    ticket_id: str,
    request: AddMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a message to a ticket."""
    try:
        support_service = SupportService(db)
        
        # Verify ticket belongs to user
        ticket = support_service.get_ticket(ticket_id, user_id=current_user.id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        message = support_service.add_message(
            ticket_id=ticket_id,
            user_id=current_user.id,
            message=request.message,
            is_internal=request.is_internal
        )
        
        return MessageResponse(
            id=message.id,
            ticket_id=message.ticket_id,
            user_id=message.user_id,
            message=message.message,
            is_internal=bool(message.is_internal),
            created_at=message.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add message error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message"
        )


@router.get("/tickets/{ticket_id}/messages", response_model=List[MessageResponse])
async def get_ticket_messages(
    ticket_id: str,
    include_internal: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a ticket."""
    try:
        support_service = SupportService(db)
        
        # Verify ticket belongs to user
        ticket = support_service.get_ticket(ticket_id, user_id=current_user.id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        messages = support_service.get_ticket_messages(
            ticket_id=ticket_id,
            include_internal=include_internal
        )
        
        return [
            MessageResponse(
                id=m.id,
                ticket_id=m.ticket_id,
                user_id=m.user_id,
                message=m.message,
                is_internal=bool(m.is_internal),
                created_at=m.created_at.isoformat()
            )
            for m in messages
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get messages error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.post("/tickets/{ticket_id}/create-from-error")
async def create_ticket_from_error(
    ticket_id: Optional[str],
    error_message: str,
    error_context: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a support ticket from an error dialog."""
    try:
        support_service = SupportService(db)
        tenant_id = getattr(current_user, 'tenant_id', None)
        
        ticket = support_service.create_ticket_from_error(
            user_id=current_user.id,
            error_message=error_message,
            error_context=error_context,
            tenant_id=tenant_id
        )
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "message": "Support ticket created successfully"
        }
    except Exception as e:
        logger.error(f"Create ticket from error error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket from error"
        )

