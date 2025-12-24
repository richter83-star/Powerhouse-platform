"""
GDPR Compliance Service

Handles data export, deletion, and consent management for GDPR compliance.
"""

import logging
import uuid
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean
from database.models import Base, User, Tenant

logger = logging.getLogger(__name__)


class ConsentRecord(Base):
    """GDPR consent record"""
    __tablename__ = "consent_records"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    
    consent_type = Column(String(100), nullable=False)  # marketing, analytics, necessary, etc.
    version = Column(String(50), nullable=False)  # Version of terms/privacy policy
    consented = Column(Boolean, default=False, nullable=False)
    consent_method = Column(String(50), nullable=True)  # web, api, email, etc.
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    record_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Renamed to avoid SQLAlchemy conflict


class DataExportRequest(Base):
    """Data export request for GDPR"""
    __tablename__ = "data_export_requests"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    format = Column(String(50), default="json", nullable=False)  # json, csv, xml
    
    file_path = Column(String(500), nullable=True)  # Path to exported file
    file_size_bytes = Column(Integer, nullable=True)
    
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # When export file expires
    
    error_message = Column(Text, nullable=True)
    record_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Renamed to avoid SQLAlchemy conflict


class DataDeletionRequest(Base):
    """Data deletion request for GDPR"""
    __tablename__ = "data_deletion_requests"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    deletion_type = Column(String(50), default="full", nullable=False)  # full, partial
    
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    verification_token = Column(String(100), nullable=True)  # For verification before deletion
    verified_at = Column(DateTime, nullable=True)
    
    error_message = Column(Text, nullable=True)
    record_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Renamed to avoid SQLAlchemy conflict


class GDPRService:
    """
    GDPR compliance service.
    
    Features:
    - Data export (right to data portability)
    - Data deletion (right to be forgotten)
    - Consent management
    - Privacy policy versioning
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        version: str,
        consented: bool,
        tenant_id: Optional[str] = None,
        consent_method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConsentRecord:
        """Record user consent."""
        # Check for existing consent
        existing = self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.consent_type == consent_type,
            ConsentRecord.revoked_at.is_(None)
        ).first()
        
        if existing:
            # Update existing
            existing.consented = consented
            existing.version = version
            existing.consent_method = consent_method
            existing.updated_at = datetime.utcnow()
            if not consented:
                existing.revoked_at = datetime.utcnow()
            consent_record = existing
        else:
            # Create new
            consent_record = ConsentRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                consent_type=consent_type,
                version=version,
                consented=consented,
                consent_method=consent_method,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.utcnow()
            )
            self.db.add(consent_record)
        
        self.db.commit()
        self.db.refresh(consent_record)
        
        return consent_record
    
    def get_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for user."""
        return self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.revoked_at.is_(None)
        ).all()
    
    def revoke_consent(self, user_id: str, consent_type: str) -> bool:
        """Revoke user consent."""
        consent = self.db.query(ConsentRecord).filter(
            ConsentRecord.user_id == user_id,
            ConsentRecord.consent_type == consent_type,
            ConsentRecord.revoked_at.is_(None)
        ).first()
        
        if consent:
            consent.consented = False
            consent.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def request_data_export(
        self,
        user_id: str,
        format: str = "json",
        tenant_id: Optional[str] = None
    ) -> DataExportRequest:
        """Request data export for user."""
        export_request = DataExportRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            status="pending",
            format=format,
            requested_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)  # Export expires in 30 days
        )
        
        self.db.add(export_request)
        self.db.commit()
        self.db.refresh(export_request)
        
        logger.info(f"Data export requested for user {user_id}")
        return export_request
    
    def export_user_data(self, user_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Export all user data.
        
        Returns:
            Dict containing all user data
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Collect all user data
        export_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "job_title": user.job_title,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "consents": [],
            "exported_at": datetime.utcnow().isoformat()
        }
        
        # Get consent records
        consents = self.get_consents(user_id)
        export_data["consents"] = [
            {
                "type": c.consent_type,
                "version": c.version,
                "consented": c.consented,
                "created_at": c.created_at.isoformat(),
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None
            }
            for c in consents
        ]
        
        # Add tenant data if applicable
        # (You would add more data sources here)
        
        return export_data
    
    def request_data_deletion(
        self,
        user_id: str,
        deletion_type: str = "full",
        tenant_id: Optional[str] = None
    ) -> DataDeletionRequest:
        """Request data deletion for user."""
        import secrets
        verification_token = secrets.token_urlsafe(32)
        
        deletion_request = DataDeletionRequest(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            status="pending",
            deletion_type=deletion_type,
            verification_token=verification_token,
            requested_at=datetime.utcnow()
        )
        
        self.db.add(deletion_request)
        self.db.commit()
        self.db.refresh(deletion_request)
        
        logger.info(f"Data deletion requested for user {user_id}")
        return deletion_request
    
    def verify_deletion_request(self, request_id: str, verification_token: str) -> bool:
        """Verify deletion request with token."""
        deletion_request = self.db.query(DataDeletionRequest).filter(
            DataDeletionRequest.id == request_id,
            DataDeletionRequest.verification_token == verification_token,
            DataDeletionRequest.status == "pending"
        ).first()
        
        if deletion_request:
            deletion_request.verified_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def delete_user_data(self, user_id: str, deletion_type: str = "full") -> Dict[str, Any]:
        """
        Delete user data.
        
        Args:
            user_id: User ID
            deletion_type: "full" or "partial"
            
        Returns:
            Dict with deletion summary
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        deletion_summary = {
            "user_id": user_id,
            "deletion_type": deletion_type,
            "deleted_at": datetime.utcnow().isoformat(),
            "items_deleted": []
        }
        
        if deletion_type == "full":
            # Delete all user data
            # Revoke all consents
            consents = self.get_consents(user_id)
            for consent in consents:
                self.revoke_consent(user_id, consent.consent_type)
                deletion_summary["items_deleted"].append(f"consent:{consent.consent_type}")
            
            # Anonymize user account (soft delete)
            user.email = f"deleted_{user.id}@deleted.local"
            user.full_name = "Deleted User"
            user.company_name = None
            user.job_title = None
            user.is_active = 0
            self.db.commit()
            
            deletion_summary["items_deleted"].append("user_account")
        
        logger.info(f"User data deleted: {user_id} (type: {deletion_type})")
        return deletion_summary

