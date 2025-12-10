"""
License Key Management System

Handles license key generation, validation, activation, and device binding.
Supports trial periods, grace periods, multi-seat licensing, and offline activation.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import platform
import json

from sqlalchemy.orm import Session
from database.models import License, LicenseActivation, LicenseStatus, LicenseType, Tenant, User


class LicenseValidationResult:
    """Result of license validation"""
    def __init__(
        self,
        valid: bool,
        status: LicenseStatus,
        message: str,
        days_remaining: Optional[int] = None,
        grace_period_days: Optional[int] = None
    ):
        self.valid = valid
        self.status = status
        self.message = message
        self.days_remaining = days_remaining
        self.grace_period_days = grace_period_days


@dataclass
class HardwareFingerprint:
    """Hardware fingerprint data"""
    machine_id: str
    processor: str
    platform: str
    architecture: str
    fingerprint: str  # Combined hash


class LicenseManager:
    """
    Manages license keys, activation, and validation.
    
    Features:
    - License key generation with cryptographic signing
    - Hardware fingerprinting for device binding
    - Trial period management
    - Grace period handling
    - Multi-seat licensing
    - Offline activation support
    - License revocation
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize license manager.
        
        Args:
            secret_key: Secret key for license signing (defaults to env var)
        """
        import os
        self.secret_key = secret_key or os.getenv("LICENSE_SECRET_KEY", "change-me-in-production")
        self.grace_period_days = 7  # Default grace period
    
    def generate_license_key(
        self,
        license_type: LicenseType = LicenseType.STANDARD,
        seats: int = 1,
        max_devices: int = 1,
        trial_days: Optional[int] = None,
        expiration_days: Optional[int] = None,
        features: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a new license key.
        
        Format: XXXX-XXXX-XXXX-XXXX-XXXX (5 groups of 4 chars)
        
        Args:
            license_type: Type of license
            seats: Number of user seats
            max_devices: Maximum number of devices
            trial_days: Trial period in days (None for non-trial)
            expiration_days: License expiration in days (None for perpetual)
            features: List of enabled features
            metadata: Additional metadata
            
        Returns:
            Generated license key string
        """
        # Generate unique identifier
        license_id = str(uuid.uuid4())
        
        # Create license data
        license_data = {
            "id": license_id,
            "type": license_type.value,
            "seats": seats,
            "max_devices": max_devices,
            "trial_days": trial_days,
            "expiration_days": expiration_days,
            "features": features or [],
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Create signature
        data_str = json.dumps(license_data, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(),
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()[:16]  # First 16 chars of hash
        
        # Combine data and signature
        combined = f"{license_id.replace('-', '')}{signature}"
        
        # Format as license key (XXXX-XXXX-XXXX-XXXX-XXXX)
        key_parts = [combined[i:i+4] for i in range(0, min(20, len(combined)), 4)]
        license_key = "-".join(key_parts).upper()
        
        # Pad to 29 chars if needed
        while len(license_key.replace("-", "")) < 20:
            license_key += "-" + secrets.token_hex(2).upper()
        
        return license_key[:29]  # Ensure exactly 29 chars (5 groups of 4 + 4 dashes)
    
    def validate_license_key_format(self, license_key: str) -> bool:
        """Validate license key format"""
        # Remove spaces and convert to uppercase
        key = license_key.replace(" ", "").replace("-", "").upper()
        return len(key) == 20 and all(c in "0123456789ABCDEF" for c in key)
    
    def get_hardware_fingerprint(self) -> HardwareFingerprint:
        """
        Generate hardware fingerprint for device binding.
        
        Uses machine ID, processor, platform, and architecture.
        """
        try:
            import platform
            machine_id = platform.node()  # Computer name
            processor = platform.processor() or platform.machine()
            platform_name = platform.system()
            architecture = platform.architecture()[0]
        except Exception:
            # Fallback values
            machine_id = "unknown"
            processor = "unknown"
            platform_name = "unknown"
            architecture = "unknown"
        
        # Create combined fingerprint
        fingerprint_data = f"{machine_id}|{processor}|{platform_name}|{architecture}"
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return HardwareFingerprint(
            machine_id=machine_id,
            processor=processor,
            platform=platform_name,
            architecture=architecture,
            fingerprint=fingerprint_hash
        )
    
    def create_license(
        self,
        db: Session,
        license_key: str,
        license_type: LicenseType = LicenseType.STANDARD,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        seats: int = 1,
        max_devices: int = 1,
        trial_days: Optional[int] = None,
        expiration_days: Optional[int] = None,
        features: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> License:
        """
        Create a new license record in database.
        
        Args:
            db: Database session
            license_key: License key string
            license_type: Type of license
            tenant_id: Associated tenant ID (optional)
            user_id: Associated user ID (optional)
            seats: Number of user seats
            max_devices: Maximum devices
            trial_days: Trial period in days
            expiration_days: Expiration in days (None for perpetual)
            features: Enabled features
            metadata: Additional metadata
            
        Returns:
            Created License object
        """
        now = datetime.utcnow()
        
        # Calculate expiration dates
        expires_at = None
        trial_ends_at = None
        
        if trial_days:
            trial_ends_at = now + timedelta(days=trial_days)
            status = LicenseStatus.TRIAL
        elif expiration_days:
            expires_at = now + timedelta(days=expiration_days)
            status = LicenseStatus.INACTIVE  # Not activated yet
        else:
            status = LicenseStatus.INACTIVE  # Perpetual, but not activated
        
        license_obj = License(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            license_key=license_key,
            license_type=license_type,
            status=status,
            issued_at=now,
            expires_at=expires_at,
            trial_ends_at=trial_ends_at,
            seats=seats,
            max_devices=max_devices,
            features=features or [],
            metadata=metadata or {}
        )
        
        db.add(license_obj)
        db.commit()
        db.refresh(license_obj)
        
        return license_obj
    
    def activate_license(
        self,
        db: Session,
        license_key: str,
        hardware_fingerprint: Optional[str] = None,
        device_name: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[License, LicenseActivation]:
        """
        Activate a license on a device.
        
        Args:
            db: Database session
            license_key: License key to activate
            hardware_fingerprint: Hardware fingerprint (auto-generated if None)
            device_name: Optional device name
            device_info: Optional device information dict
            ip_address: IP address of activation
            user_agent: User agent string
            
        Returns:
            Tuple of (License, LicenseActivation)
            
        Raises:
            ValueError: If license is invalid or cannot be activated
        """
        # Get hardware fingerprint if not provided
        if not hardware_fingerprint:
            hw = self.get_hardware_fingerprint()
            hardware_fingerprint = hw.fingerprint
            if not device_info:
                device_info = {
                    "machine_id": hw.machine_id,
                    "processor": hw.processor,
                    "platform": hw.platform,
                    "architecture": hw.architecture
                }
        
        # Find license
        license_obj = db.query(License).filter(License.license_key == license_key).first()
        if not license_obj:
            raise ValueError("License key not found")
        
        # Check if already activated on this device
        existing_activation = db.query(LicenseActivation).filter(
            LicenseActivation.license_id == license_obj.id,
            LicenseActivation.hardware_fingerprint == hardware_fingerprint,
            LicenseActivation.is_active == 1
        ).first()
        
        if existing_activation:
            # Update last validated time
            existing_activation.last_validated_at = datetime.utcnow()
            db.commit()
            return license_obj, existing_activation
        
        # Check device limit
        active_activations = db.query(LicenseActivation).filter(
            LicenseActivation.license_id == license_obj.id,
            LicenseActivation.is_active == 1
        ).count()
        
        if active_activations >= license_obj.max_devices:
            raise ValueError(f"License has reached maximum device limit ({license_obj.max_devices})")
        
        # Validate license status
        validation = self.validate_license(db, license_key, hardware_fingerprint)
        if not validation.valid:
            raise ValueError(f"License cannot be activated: {validation.message}")
        
        # Create activation record
        activation = LicenseActivation(
            id=str(uuid.uuid4()),
            license_id=license_obj.id,
            hardware_fingerprint=hardware_fingerprint,
            device_name=device_name,
            device_info=device_info or {},
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=1,
            activated_at=datetime.utcnow(),
            last_validated_at=datetime.utcnow()
        )
        
        # Update license
        if license_obj.status == LicenseStatus.INACTIVE:
            license_obj.status = LicenseStatus.ACTIVE
            license_obj.activated_at = datetime.utcnow()
        
        license_obj.hardware_fingerprint = hardware_fingerprint
        license_obj.device_count = active_activations + 1
        
        db.add(activation)
        db.commit()
        db.refresh(activation)
        db.refresh(license_obj)
        
        return license_obj, activation
    
    def validate_license(
        self,
        db: Session,
        license_key: str,
        hardware_fingerprint: Optional[str] = None
    ) -> LicenseValidationResult:
        """
        Validate a license key.
        
        Args:
            db: Database session
            license_key: License key to validate
            hardware_fingerprint: Hardware fingerprint (optional, for device binding check)
            
        Returns:
            LicenseValidationResult
        """
        # Find license
        license_obj = db.query(License).filter(License.license_key == license_key).first()
        if not license_obj:
            return LicenseValidationResult(
                valid=False,
                status=LicenseStatus.INACTIVE,
                message="License key not found"
            )
        
        now = datetime.utcnow()
        
        # Check if revoked
        if license_obj.status == LicenseStatus.REVOKED:
            return LicenseValidationResult(
                valid=False,
                status=LicenseStatus.REVOKED,
                message="License has been revoked"
            )
        
        # Check hardware fingerprint if provided
        if hardware_fingerprint:
            # Check if activated on this device
            activation = db.query(LicenseActivation).filter(
                LicenseActivation.license_id == license_obj.id,
                LicenseActivation.hardware_fingerprint == hardware_fingerprint,
                LicenseActivation.is_active == 1
            ).first()
            
            if not activation:
                return LicenseValidationResult(
                    valid=False,
                    status=license_obj.status,
                    message="License not activated on this device"
                )
            
            # Update last validated time
            activation.last_validated_at = now
            db.commit()
        
        # Check trial period
        if license_obj.trial_ends_at:
            if now > license_obj.trial_ends_at:
                # Trial expired
                if license_obj.status == LicenseStatus.TRIAL:
                    license_obj.status = LicenseStatus.EXPIRED
                    db.commit()
                
                return LicenseValidationResult(
                    valid=False,
                    status=LicenseStatus.EXPIRED,
                    message="Trial period has expired"
                )
            
            days_remaining = (license_obj.trial_ends_at - now).days
            return LicenseValidationResult(
                valid=True,
                status=LicenseStatus.TRIAL,
                message=f"Trial license active ({days_remaining} days remaining)",
                days_remaining=days_remaining
            )
        
        # Check expiration
        if license_obj.expires_at:
            if now > license_obj.expires_at:
                # Check grace period
                if license_obj.grace_period_ends_at and now <= license_obj.grace_period_ends_at:
                    grace_days = (license_obj.grace_period_ends_at - now).days
                    if license_obj.status != LicenseStatus.GRACE_PERIOD:
                        license_obj.status = LicenseStatus.GRACE_PERIOD
                        db.commit()
                    
                    return LicenseValidationResult(
                        valid=True,
                        status=LicenseStatus.GRACE_PERIOD,
                        message=f"License expired, grace period active ({grace_days} days remaining)",
                        grace_period_days=grace_days
                    )
                else:
                    # Fully expired
                    if license_obj.status != LicenseStatus.EXPIRED:
                        license_obj.status = LicenseStatus.EXPIRED
                        db.commit()
                    
                    return LicenseValidationResult(
                        valid=False,
                        status=LicenseStatus.EXPIRED,
                        message="License has expired"
                    )
            
            days_remaining = (license_obj.expires_at - now).days
            return LicenseValidationResult(
                valid=True,
                status=LicenseStatus.ACTIVE,
                message=f"License active ({days_remaining} days remaining)",
                days_remaining=days_remaining
            )
        
        # Perpetual license
        if license_obj.status == LicenseStatus.ACTIVE:
            return LicenseValidationResult(
                valid=True,
                status=LicenseStatus.ACTIVE,
                message="License active (perpetual)"
            )
        
        return LicenseValidationResult(
            valid=False,
            status=license_obj.status,
            message="License not activated"
        )
    
    def revoke_license(
        self,
        db: Session,
        license_key: str,
        reason: Optional[str] = None
    ) -> License:
        """
        Revoke a license.
        
        Args:
            db: Database session
            license_key: License key to revoke
            reason: Reason for revocation
            
        Returns:
            Updated License object
        """
        license_obj = db.query(License).filter(License.license_key == license_key).first()
        if not license_obj:
            raise ValueError("License key not found")
        
        license_obj.status = LicenseStatus.REVOKED
        license_obj.revoked_at = datetime.utcnow()
        license_obj.revocation_reason = reason
        
        # Deactivate all activations
        activations = db.query(LicenseActivation).filter(
            LicenseActivation.license_id == license_obj.id,
            LicenseActivation.is_active == 1
        ).all()
        
        for activation in activations:
            activation.is_active = 0
            activation.deactivated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(license_obj)
        
        return license_obj
    
    def deactivate_device(
        self,
        db: Session,
        license_key: str,
        hardware_fingerprint: str
    ) -> bool:
        """
        Deactivate a license on a specific device.
        
        Args:
            db: Database session
            license_key: License key
            hardware_fingerprint: Hardware fingerprint of device to deactivate
            
        Returns:
            True if deactivated, False if not found
        """
        license_obj = db.query(License).filter(License.license_key == license_key).first()
        if not license_obj:
            return False
        
        activation = db.query(LicenseActivation).filter(
            LicenseActivation.license_id == license_obj.id,
            LicenseActivation.hardware_fingerprint == hardware_fingerprint,
            LicenseActivation.is_active == 1
        ).first()
        
        if not activation:
            return False
        
        activation.is_active = 0
        activation.deactivated_at = datetime.utcnow()
        license_obj.device_count = max(0, license_obj.device_count - 1)
        
        db.commit()
        return True
    
    def get_license_info(
        self,
        db: Session,
        license_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed license information.
        
        Args:
            db: Database session
            license_key: License key
            
        Returns:
            License information dict or None
        """
        license_obj = db.query(License).filter(License.license_key == license_key).first()
        if not license_obj:
            return None
        
        validation = self.validate_license(db, license_key)
        
        activations = db.query(LicenseActivation).filter(
            LicenseActivation.license_id == license_obj.id,
            LicenseActivation.is_active == 1
        ).all()
        
        return {
            "license_key": license_obj.license_key,
            "type": license_obj.license_type.value,
            "status": license_obj.status.value,
            "seats": license_obj.seats,
            "max_devices": license_obj.max_devices,
            "device_count": license_obj.device_count,
            "features": license_obj.features,
            "issued_at": license_obj.issued_at.isoformat() if license_obj.issued_at else None,
            "activated_at": license_obj.activated_at.isoformat() if license_obj.activated_at else None,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            "trial_ends_at": license_obj.trial_ends_at.isoformat() if license_obj.trial_ends_at else None,
            "validation": {
                "valid": validation.valid,
                "message": validation.message,
                "days_remaining": validation.days_remaining,
                "grace_period_days": validation.grace_period_days
            },
            "activations": [
                {
                    "device_name": a.device_name,
                    "activated_at": a.activated_at.isoformat(),
                    "last_validated_at": a.last_validated_at.isoformat() if a.last_validated_at else None
                }
                for a in activations
            ]
        }

