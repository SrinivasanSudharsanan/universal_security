#!/usr/bin/env python3
"""
Password utilities for secure password hashing
"""

import hashlib
import secrets
import base64
from typing import Tuple

class PasswordManager:
    """Manage password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """
        Hash a password with a random salt
        Returns: (password_hash, salt)
        """
        # Generate random salt
        salt = secrets.token_hex(32)
        
        # Create password hash using SHA-256
        password_salted = password + salt
        password_hash = hashlib.sha256(password_salted.encode()).hexdigest()
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """
        Verify a password against stored hash and salt
        """
        if not all([password, stored_hash, salt]):
            return False
            
        # Hash the provided password with the stored salt
        password_salted = password + salt
        computed_hash = hashlib.sha256(password_salted.encode()).hexdigest()
        
        # Compare hashes (constant-time comparison to prevent timing attacks)
        return secrets.compare_digest(computed_hash, stored_hash)
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a secure random password
        """
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
