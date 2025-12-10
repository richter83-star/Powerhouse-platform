"""
IP Whitelisting Service

Provides IP-based access control for enterprise customers.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from database.models import Base, Tenant

logger = logging.getLogger(__name__)


class IPWhitelist(Base):
    """IP whitelist entry"""
    __tablename__ = "ip_whitelists"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    ip_address = Column(String(45), nullable=False, index=True)  # IPv4 or IPv6
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")


class IPWhitelistService:
    """
    IP whitelisting service.
    
    Features:
    - IP address whitelisting
    - CIDR range support
    - Per-tenant whitelists
    - Enterprise-only feature
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_ip(
        self,
        tenant_id: str,
        ip_address: str,
        description: Optional[str] = None
    ) -> IPWhitelist:
        """Add IP address to whitelist."""
        import uuid
        
        whitelist_entry = IPWhitelist(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            ip_address=ip_address,
            description=description,
            is_active=True
        )
        
        self.db.add(whitelist_entry)
        self.db.commit()
        self.db.refresh(whitelist_entry)
        
        return whitelist_entry
    
    def remove_ip(self, whitelist_id: str) -> bool:
        """Remove IP from whitelist."""
        entry = self.db.query(IPWhitelist).filter(IPWhitelist.id == whitelist_id).first()
        if entry:
            self.db.delete(entry)
            self.db.commit()
            return True
        return False
    
    def get_whitelist(self, tenant_id: str) -> List[IPWhitelist]:
        """Get all whitelisted IPs for tenant."""
        return self.db.query(IPWhitelist).filter(
            IPWhitelist.tenant_id == tenant_id,
            IPWhitelist.is_active == True
        ).all()
    
    def is_ip_allowed(self, tenant_id: str, ip_address: str) -> bool:
        """
        Check if IP address is allowed.
        
        Args:
            tenant_id: Tenant ID
            ip_address: IP address to check
            
        Returns:
            True if allowed, False otherwise
        """
        whitelist = self.get_whitelist(tenant_id)
        
        if not whitelist:
            # No whitelist = all IPs allowed
            return True
        
        # Check if IP matches any whitelist entry
        for entry in whitelist:
            if self._ip_matches(ip_address, entry.ip_address):
                return True
        
        return False
    
    def _ip_matches(self, ip: str, pattern: str) -> bool:
        """
        Check if IP matches pattern (supports CIDR notation).
        
        Args:
            ip: IP address to check
            pattern: IP pattern (can be CIDR notation)
            
        Returns:
            True if matches
        """
        if '/' in pattern:
            # CIDR notation
            try:
                import ipaddress
                ip_obj = ipaddress.ip_address(ip)
                network = ipaddress.ip_network(pattern, strict=False)
                return ip_obj in network
            except Exception:
                return False
        else:
            # Exact match
            return ip == pattern

