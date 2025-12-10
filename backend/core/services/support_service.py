"""
Customer Support Service

Handles support tickets, chat, and knowledge base integration.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLEnum, ForeignKey
from database.models import Base, User

logger = logging.getLogger(__name__)


class TicketStatus(str, Enum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Support ticket priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicket(Base):
    """Support ticket model"""
    __tablename__ = "support_tickets"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    
    category = Column(String(100), nullable=True)  # bug, feature_request, billing, etc.
    tags = Column(JSON, default=list, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    assigned_to = Column(String(36), nullable=True)  # Support agent user ID
    ticket_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Renamed to avoid SQLAlchemy conflict


class SupportMessage(Base):
    """Support ticket message/comment"""
    __tablename__ = "support_messages"
    
    id = Column(String(36), primary_key=True)
    ticket_id = Column(String(36), ForeignKey("support_tickets.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    message = Column(Text, nullable=False)
    is_internal = Column(Integer, default=0, nullable=False)  # 1=internal note, 0=customer visible
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ticket_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Renamed to avoid SQLAlchemy conflict


class SupportService:
    """
    Customer support service.
    
    Features:
    - Ticket creation and management
    - Message threading
    - Priority handling
    - Integration with external ticketing systems (Zendesk, Intercom)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_ticket(
        self,
        user_id: str,
        subject: str,
        description: str,
        tenant_id: Optional[str] = None,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> SupportTicket:
        """Create a new support ticket."""
        ticket = SupportTicket(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            subject=subject,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            category=category,
            tags=tags or [],
            created_at=datetime.utcnow(),
            metadata={}
        )
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        
        logger.info(f"Support ticket created: {ticket.id} by user {user_id}")
        return ticket
    
    def add_message(
        self,
        ticket_id: str,
        user_id: str,
        message: str,
        is_internal: bool = False
    ) -> SupportMessage:
        """Add a message to a ticket."""
        support_message = SupportMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            user_id=user_id,
            message=message,
            is_internal=1 if is_internal else 0,
            created_at=datetime.utcnow(),
            metadata={}
        )
        
        # Update ticket status if customer replied
        ticket = self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if ticket and not is_internal:
            if ticket.status == TicketStatus.WAITING_CUSTOMER:
                ticket.status = TicketStatus.IN_PROGRESS
            ticket.updated_at = datetime.utcnow()
        
        self.db.add(support_message)
        self.db.commit()
        self.db.refresh(support_message)
        
        return support_message
    
    def update_ticket_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        assigned_to: Optional[str] = None
    ) -> Optional[SupportTicket]:
        """Update ticket status."""
        ticket = self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not ticket:
            return None
        
        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        
        if assigned_to:
            ticket.assigned_to = assigned_to
        
        if status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(ticket)
        
        return ticket
    
    def get_user_tickets(
        self,
        user_id: str,
        status: Optional[TicketStatus] = None,
        limit: int = 50
    ) -> List[SupportTicket]:
        """Get tickets for a user."""
        query = self.db.query(SupportTicket).filter(SupportTicket.user_id == user_id)
        
        if status:
            query = query.filter(SupportTicket.status == status)
        
        query = query.order_by(SupportTicket.created_at.desc()).limit(limit)
        
        return query.all()
    
    def get_ticket(self, ticket_id: str, user_id: Optional[str] = None) -> Optional[SupportTicket]:
        """Get a ticket by ID."""
        query = self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id)
        
        if user_id:
            query = query.filter(SupportTicket.user_id == user_id)
        
        return query.first()
    
    def get_ticket_messages(
        self,
        ticket_id: str,
        include_internal: bool = False
    ) -> List[SupportMessage]:
        """Get messages for a ticket."""
        query = self.db.query(SupportMessage).filter(SupportMessage.ticket_id == ticket_id)
        
        if not include_internal:
            query = query.filter(SupportMessage.is_internal == 0)
        
        return query.order_by(SupportMessage.created_at.asc()).all()
    
    def create_ticket_from_error(
        self,
        user_id: str,
        error_message: str,
        error_context: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> SupportTicket:
        """Create a support ticket from an error dialog."""
        subject = f"Error Report: {error_message[:100]}"
        description = f"""
Error occurred in Powerhouse application.

Error: {error_message}

Context:
{self._format_context(error_context)}

This ticket was automatically created from an error dialog.
        """.strip()
        
        return self.create_ticket(
            user_id=user_id,
            subject=subject,
            description=description,
            tenant_id=tenant_id,
            priority=TicketPriority.HIGH,
            category="bug",
            tags=["auto-generated", "error"]
        )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format error context for ticket description."""
        lines = []
        for key, value in context.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

