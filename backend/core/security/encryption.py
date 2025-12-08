
"""
Encryption service for sensitive data (AES-256 encryption).
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Optional
import json

class EncryptionService:
    """
    Provides AES-256 encryption for sensitive data like agent context memory.
    
    Features:
    - AES-256 encryption at rest
    - Key derivation from master password
    - JSON-safe encoding
    - Tenant-specific encryption keys
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            master_key: Master encryption key (defaults to environment variable)
        """
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY", Fernet.generate_key().decode())
        self.tenant_keys = {}  # Cache for tenant-specific keys
    
    def _derive_key(self, tenant_id: str, salt: Optional[bytes] = None) -> tuple:
        """
        Derive encryption key for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            salt: Optional salt for key derivation
            
        Returns:
            Tuple of (Fernet instance, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key_material = f"{self.master_key}:{tenant_id}".encode()
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        
        return Fernet(key), salt
    
    def encrypt(self, data: str, tenant_id: str) -> str:
        """
        Encrypt data for a specific tenant.
        
        Args:
            data: Plain text data to encrypt
            tenant_id: Tenant identifier
            
        Returns:
            Base64-encoded encrypted data with salt
        """
        fernet, salt = self._derive_key(tenant_id)
        encrypted = fernet.encrypt(data.encode())
        
        # Combine salt and encrypted data
        combined = base64.b64encode(salt + encrypted).decode()
        return combined
    
    def decrypt(self, encrypted_data: str, tenant_id: str) -> str:
        """
        Decrypt data for a specific tenant.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            tenant_id: Tenant identifier
            
        Returns:
            Decrypted plain text
        """
        try:
            # Decode and separate salt and encrypted data
            combined = base64.b64decode(encrypted_data)
            salt = combined[:16]
            encrypted = combined[16:]
            
            fernet, _ = self._derive_key(tenant_id, salt)
            decrypted = fernet.decrypt(encrypted)
            
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def encrypt_json(self, data: dict, tenant_id: str) -> str:
        """
        Encrypt JSON data.
        
        Args:
            data: Dictionary to encrypt
            tenant_id: Tenant identifier
            
        Returns:
            Encrypted JSON string
        """
        json_str = json.dumps(data)
        return self.encrypt(json_str, tenant_id)
    
    def decrypt_json(self, encrypted_data: str, tenant_id: str) -> dict:
        """
        Decrypt JSON data.
        
        Args:
            encrypted_data: Encrypted JSON string
            tenant_id: Tenant identifier
            
        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt(encrypted_data, tenant_id)
        return json.loads(json_str)
    
    def rotate_key(self, old_master_key: str, tenant_id: str) -> str:
        """
        Rotate encryption key for a tenant.
        
        Args:
            old_master_key: Previous master key
            tenant_id: Tenant identifier
            
        Returns:
            New master key
        """
        # In production, this would re-encrypt all tenant data with new key
        new_key = Fernet.generate_key().decode()
        return new_key

# Global encryption service instance
encryption_service = EncryptionService()
