#!/usr/bin/env python3
"""
Security service for Universal Security Framework
"""

import logging
from typing import List, Optional, Dict, Any
from app.utils.db_utils import execute_query, fetch_one, fetch_all

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
                SELECT user_id, username, email, is_active, created_at
                FROM security_users 
                WHERE username = $1
            """, username)
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
    
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
