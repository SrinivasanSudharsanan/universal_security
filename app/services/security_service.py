#!/usr/bin/env python3
"""
Security service for Universal Security Framework
"""

import logging
from typing import List, Optional, Dict, Any
from app.utils.db_utils import execute_query, fetch_one, fetch_all
from app.utils.password_utils import PasswordManager

logger = logging.getLogger(__name__)

class SecurityService:
    """Service for security-related database operations"""
    
    @staticmethod
    async def get_user_roles(user_id: str) -> List[str]:
        """Get all roles for a user"""
        try:
            results = await execute_query("""
                SELECT r.role_name 
                FROM security_user_roles ur
                JOIN security_roles r ON ur.role_id = r.role_id
                WHERE ur.user_id = $1
            """, user_id)
            
            return [row['role_name'] for row in results]
        except Exception as e:
            logger.error(f"Error getting user roles for {user_id}: {e}")
            return []
    
    @staticmethod
    async def get_all_roles() -> List[Dict[str, Any]]:
        """Get all security roles"""
        try:
            return await execute_query("""
                SELECT role_id, role_name, description, is_system_role
                FROM security_roles 
                ORDER BY role_name
            """)
        except Exception as e:
            logger.error(f"Error getting all roles: {e}")
            return []
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            return await fetch_one("""
                SELECT user_id, username, email, is_active, created_at, password_hash, password_salt
                FROM security_users 
                WHERE username = $1
            """, username)
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> bool:
        """Authenticate user with password"""
        try:
            user = await SecurityService.get_user_by_username(username)
            if not user or not user['is_active']:
                return False
            
            # Check if password_hash exists
            if not user.get('password_hash') or not user.get('password_salt'):
                logger.warning(f"User {username} has no password set")
                return False
            
            # Verify password
            return PasswordManager.verify_password(
                password, 
                user['password_hash'], 
                user['password_salt']
            )
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return False
    
    @staticmethod
    async def set_user_password(username: str, password: str) -> bool:
        """Set or update user password"""
        try:
            user = await SecurityService.get_user_by_username(username)
            if not user:
                return False
            
            # Hash the new password
            password_hash, salt = PasswordManager.hash_password(password)
            
            # Update in database
            await execute_query("""
                UPDATE security_users 
                SET password_hash = $1, password_salt = $2 
                WHERE username = $3
            """, password_hash, salt, username)
            
            logger.info(f"Password updated for user {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting password for {username}: {e}")
            return False
    
    @staticmethod
    async def create_user(user_id: str, username: str, email: str, password: str, role_names: List[str] = None) -> bool:
        """Create a new user with hashed password"""
        try:
            # Hash the password
            password_hash, salt = PasswordManager.hash_password(password)
            
            # Insert user
            await execute_query("""
                INSERT INTO security_users (user_id, username, email, password_hash, password_salt)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, username, email, password_hash, salt)
            
            # Assign roles if provided
            if role_names:
                for role_name in role_names:
                    await execute_query("""
                        INSERT INTO security_user_roles (user_id, role_id)
                        VALUES ($1, (SELECT role_id FROM security_roles WHERE role_name = $2))
                        ON CONFLICT (user_id, role_id) DO NOTHING
                    """, user_id, role_name)
            
            logger.info(f"User {username} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return False
    
    @staticmethod
    async def get_data_sources() -> List[Dict[str, Any]]:
        """Get all data sources"""
        try:
            return await execute_query("""
                SELECT source_id, source_name, engine_type, is_active
                FROM security_data_sources 
                ORDER BY source_name
            """)
        except Exception as e:
            logger.error(f"Error getting data sources: {e}")
            return []
    
    @staticmethod
    async def verify_user_access(username: str, required_role: str = None) -> bool:
        """Verify if user exists and has required role"""
        try:
            user = await SecurityService.get_user_by_username(username)
            if not user or not user['is_active']:
                return False
            
            if required_role:
                user_roles = await SecurityService.get_user_roles(user['user_id'])
                return required_role in user_roles
            
            return True
        except Exception as e:
            logger.error(f"Error verifying user access for {username}: {e}")
            return False
