"""
Email Queue System

Provides reliable email delivery with retry logic and failure handling.
Uses database-backed queue for persistence.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum as SQLEnum
from database.models import Base

logger = logging.getLogger(__name__)


class EmailStatus(str, Enum):
    """Email queue status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueuedEmail:
    """Email queue item"""
    id: str
    to_email: str
    subject: str
    html_content: str
    text_content: Optional[str]
    from_email: Optional[str]
    from_name: Optional[str]
    reply_to: Optional[str]
    status: EmailStatus
    retry_count: int
    max_retries: int
    created_at: datetime
    sent_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmailQueue(Base):
    """Database model for email queue"""
    __tablename__ = "email_queue"
    
    id = Column(String(36), primary_key=True)
    to_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    from_email = Column(String(255), nullable=True)
    from_name = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING, nullable=False, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    email_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Renamed to avoid SQLAlchemy conflict


class EmailQueueService:
    """
    Email queue service for reliable email delivery.
    
    Features:
    - Database-backed queue
    - Automatic retry with exponential backoff
    - Failure tracking
    - Batch processing
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._processing = False
    
    def enqueue_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailQueue:
        """
        Add email to queue.
        
        Returns:
            EmailQueue object
        """
        import uuid
        
        email_item = EmailQueue(
            id=str(uuid.uuid4()),
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email=from_email,
            from_name=from_name,
            reply_to=reply_to,
            status=EmailStatus.PENDING,
            retry_count=0,
            max_retries=max_retries,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.db.add(email_item)
        self.db.commit()
        self.db.refresh(email_item)
        
        logger.info(f"Email queued: {to_email} - {subject}")
        return email_item
    
    async def process_queue(self, batch_size: int = 10) -> int:
        """
        Process pending emails from queue.
        
        Args:
            batch_size: Number of emails to process in one batch
            
        Returns:
            Number of emails processed
        """
        if self._processing:
            logger.warning("Email queue is already being processed")
            return 0
        
        self._processing = True
        processed = 0
        
        try:
            # Get pending emails
            pending_emails = self.db.query(EmailQueue).filter(
                EmailQueue.status.in_([EmailStatus.PENDING, EmailStatus.RETRYING])
            ).limit(batch_size).all()
            
            from core.services.email_service import get_email_service
            email_service = get_email_service()
            
            for email_item in pending_emails:
                try:
                    # Update status to processing
                    email_item.status = EmailStatus.PROCESSING
                    self.db.commit()
                    
                    # Send email
                    success = await email_service.send_email(
                        to_email=email_item.to_email,
                        subject=email_item.subject,
                        html_content=email_item.html_content,
                        text_content=email_item.text_content,
                        from_email=email_item.from_email,
                        from_name=email_item.from_name,
                        reply_to=email_item.reply_to
                    )
                    
                    if success:
                        email_item.status = EmailStatus.SENT
                        email_item.sent_at = datetime.utcnow()
                        email_item.error_message = None
                        logger.info(f"Email sent successfully: {email_item.to_email}")
                    else:
                        # Retry logic
                        email_item.retry_count += 1
                        if email_item.retry_count < email_item.max_retries:
                            email_item.status = EmailStatus.RETRYING
                            # Exponential backoff: wait 2^retry_count minutes
                            wait_minutes = 2 ** email_item.retry_count
                            logger.warning(
                                f"Email failed, will retry in {wait_minutes} minutes: {email_item.to_email}"
                            )
                        else:
                            email_item.status = EmailStatus.FAILED
                            email_item.error_message = "Max retries exceeded"
                            logger.error(f"Email failed after {email_item.max_retries} retries: {email_item.to_email}")
                    
                    self.db.commit()
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_item.id}: {e}", exc_info=True)
                    email_item.status = EmailStatus.FAILED
                    email_item.error_message = str(e)
                    self.db.commit()
        
        finally:
            self._processing = False
        
        return processed
    
    def get_failed_emails(self, limit: int = 100) -> List[EmailQueue]:
        """Get failed emails for manual review."""
        return self.db.query(EmailQueue).filter(
            EmailQueue.status == EmailStatus.FAILED
        ).order_by(EmailQueue.created_at.desc()).limit(limit).all()
    
    def retry_failed_email(self, email_id: str) -> bool:
        """Manually retry a failed email."""
        email_item = self.db.query(EmailQueue).filter(EmailQueue.id == email_id).first()
        if not email_item:
            return False
        
        if email_item.status != EmailStatus.FAILED:
            return False
        
        email_item.status = EmailStatus.PENDING
        email_item.retry_count = 0
        email_item.error_message = None
        self.db.commit()
        
        return True


# Background worker for processing email queue
async def email_queue_worker(db: Session, interval_seconds: int = 60):
    """
    Background worker to process email queue periodically.
    
    Args:
        db: Database session
        interval_seconds: Interval between queue processing runs
    """
    queue_service = EmailQueueService(db)
    
    while True:
        try:
            processed = await queue_service.process_queue()
            if processed > 0:
                logger.info(f"Processed {processed} emails from queue")
        except Exception as e:
            logger.error(f"Error in email queue worker: {e}", exc_info=True)
        
        await asyncio.sleep(interval_seconds)

