#!/usr/bin/env python3
"""
Encryption Manager for sensitive data storage
Uses AES-256-GCM for authenticated encryption
"""

import os
import base64
import json
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption/decryption of sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        # In production, get master key from secure storage (HashiCorp Vault, AWS KMS, etc.)
        self.master_key = master_key or os.getenv('SECURITY_MASTER_KEY')
        if not self.master_key:
            # For development only - in production this should be from secure source
            self.master_key = "dev-master-key-change-in-production-32bytes!"
        
        # Ensure master key is 32 bytes for AES-256
        if len(self.master_key) < 32:
            self.master_key = self.master_key.ljust(32, '0')[:32]
        elif len(self.master_key) > 32:
            self.master_key = self.master_key[:32]
    
    def derive_key(self, salt: bytes, context: str = "") -> bytes:
        """Derive a context-specific key from master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.master_key.encode() + context.encode())
    
    def encrypt_value(self, plaintext: str, context: str = "default") -> Dict[str, str]:
        """Encrypt a string value"""
        try:
            # Generate random salt and nonce
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)  # GCM recommended nonce size
            
            # Derive context-specific key
            key = self.derive_key(salt, context)
            
            # Encrypt using AES-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
            
            # Return encoded components
            return {
                'ciphertext': base64.b64encode(ciphertext).decode(),
                'salt': base64.b64encode(salt).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'context': context,
                'version': '1.0'
            }
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_value(self, encrypted_data: Dict[str, str]) -> str:
        """Decrypt an encrypted value"""
        try:
            # Extract components
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            salt = base64.b64decode(encrypted_data['salt'])
            nonce = base64.b64decode(encrypted_data['nonce'])
            context = encrypted_data.get('context', 'default')
            
            # Derive the same key
            key = self.derive_key(salt, context)
            
            # Decrypt
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_json(self, data: Dict[str, Any], context: str = "default") -> Dict[str, str]:
        """Encrypt a JSON object"""
        plaintext = json.dumps(data)
        return self.encrypt_value(plaintext, context)
    
    def decrypt_json(self, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt to JSON object"""
        plaintext = self.decrypt_value(encrypted_data)
        return json.loads(plaintext)

# Singleton instance
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """Get singleton encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
