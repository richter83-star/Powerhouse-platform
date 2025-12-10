"""
White-Label Service

Enables custom branding for enterprise customers.
Enterprise-only feature.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Boolean
from database.models import Base, Tenant

logger = logging.getLogger(__name__)


class WhiteLabelConfig(Base):
    """White-label configuration for tenants"""
    __tablename__ = "white_label_configs"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    secondary_color = Column(String(7), nullable=True)
    accent_color = Column(String(7), nullable=True)
    
    # Custom domain
    custom_domain = Column(String(255), nullable=True, unique=True, index=True)
    custom_subdomain = Column(String(100), nullable=True, unique=True, index=True)
    
    # Branding text
    company_name = Column(String(255), nullable=True)
    product_name = Column(String(255), nullable=True)
    tagline = Column(String(500), nullable=True)
    
    # Email branding
    email_from_name = Column(String(255), nullable=True)
    email_from_address = Column(String(255), nullable=True)
    email_template_customization = Column(JSON, default=dict, nullable=False)
    
    # UI customization
    hide_powered_by = Column(Boolean, default=False, nullable=False)
    custom_css = Column(Text, nullable=True)
    custom_footer = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=False, nullable=False)
    enabled_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<WhiteLabelConfig(tenant_id={self.tenant_id}, active={self.is_active})>"


class WhiteLabelService:
    """
    White-label service for enterprise customers.
    
    Features:
    - Custom branding (logo, colors, domain)
    - Custom email templates
    - Remove "Powered by Powerhouse" branding
    - Custom subdomain support
    - Enterprise-only feature
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, tenant_id: str) -> Optional[WhiteLabelConfig]:
        """Get white-label configuration for tenant."""
        return self.db.query(WhiteLabelConfig).filter(
            WhiteLabelConfig.tenant_id == tenant_id
        ).first()
    
    def create_or_update_config(
        self,
        tenant_id: str,
        logo_url: Optional[str] = None,
        favicon_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        accent_color: Optional[str] = None,
        custom_domain: Optional[str] = None,
        custom_subdomain: Optional[str] = None,
        company_name: Optional[str] = None,
        product_name: Optional[str] = None,
        tagline: Optional[str] = None,
        email_from_name: Optional[str] = None,
        email_from_address: Optional[str] = None,
        hide_powered_by: bool = False,
        custom_css: Optional[str] = None,
        custom_footer: Optional[str] = None,
        is_active: bool = True
    ) -> WhiteLabelConfig:
        """Create or update white-label configuration."""
        config = self.get_config(tenant_id)
        
        if config:
            # Update existing
            if logo_url is not None:
                config.logo_url = logo_url
            if favicon_url is not None:
                config.favicon_url = favicon_url
            if primary_color is not None:
                config.primary_color = primary_color
            if secondary_color is not None:
                config.secondary_color = secondary_color
            if accent_color is not None:
                config.accent_color = accent_color
            if custom_domain is not None:
                config.custom_domain = custom_domain
            if custom_subdomain is not None:
                config.custom_subdomain = custom_subdomain
            if company_name is not None:
                config.company_name = company_name
            if product_name is not None:
                config.product_name = product_name
            if tagline is not None:
                config.tagline = tagline
            if email_from_name is not None:
                config.email_from_name = email_from_name
            if email_from_address is not None:
                config.email_from_address = email_from_address
            config.hide_powered_by = hide_powered_by
            if custom_css is not None:
                config.custom_css = custom_css
            if custom_footer is not None:
                config.custom_footer = custom_footer
            config.is_active = is_active
            if is_active and not config.enabled_at:
                config.enabled_at = datetime.utcnow()
            config.updated_at = datetime.utcnow()
        else:
            # Create new
            config = WhiteLabelConfig(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                logo_url=logo_url,
                favicon_url=favicon_url,
                primary_color=primary_color,
                secondary_color=secondary_color,
                accent_color=accent_color,
                custom_domain=custom_domain,
                custom_subdomain=custom_subdomain,
                company_name=company_name,
                product_name=product_name,
                tagline=tagline,
                email_from_name=email_from_name,
                email_from_address=email_from_address,
                hide_powered_by=hide_powered_by,
                custom_css=custom_css,
                custom_footer=custom_footer,
                is_active=is_active,
                enabled_at=datetime.utcnow() if is_active else None
            )
            self.db.add(config)
        
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def get_branding_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get branding configuration for tenant.
        
        Returns default branding if white-label not configured.
        """
        config = self.get_config(tenant_id)
        
        if not config or not config.is_active:
            # Return default branding
            return {
                "logo_url": "/logo.png",
                "favicon_url": "/favicon.ico",
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
                "company_name": "Powerhouse",
                "product_name": "Powerhouse Platform",
                "tagline": "AI-Powered Multi-Agent Platform",
                "hide_powered_by": False
            }
        
        return {
            "logo_url": config.logo_url or "/logo.png",
            "favicon_url": config.favicon_url or "/favicon.ico",
            "primary_color": config.primary_color or "#667eea",
            "secondary_color": config.secondary_color or "#764ba2",
            "accent_color": config.accent_color,
            "company_name": config.company_name or "Powerhouse",
            "product_name": config.product_name or "Powerhouse Platform",
            "tagline": config.tagline,
            "custom_domain": config.custom_domain,
            "custom_subdomain": config.custom_subdomain,
            "email_from_name": config.email_from_name,
            "email_from_address": config.email_from_address,
            "hide_powered_by": config.hide_powered_by,
            "custom_css": config.custom_css,
            "custom_footer": config.custom_footer
        }

