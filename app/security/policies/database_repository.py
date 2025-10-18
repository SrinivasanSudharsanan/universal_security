#!/usr/bin/env python3
"""
Database Repository for Security Policies
Uses your existing db_utils and follows your patterns
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Use your existing utilities
from app.utils import db_utils
from app.security.policies.policy_manager import DataEngine

logger = logging.getLogger(__name__)

@dataclass
class DatabaseSecurityPolicy:
    """Security policy from database"""
    user_id: str
    rls_filters: Dict[str, str]
    allowed_columns: Dict[str, List[str]]
    blocked_columns: Dict[str, List[str]]
    masked_columns: Dict[str, Dict[str, str]]
    max_rows: int
    query_timeout: int
    allowed_engines: List[DataEngine]

class DatabasePolicyRepository:
    """Repository using your existing db_utils patterns"""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
    
    async def get_user_policies(self, user_id: str) -> DatabaseSecurityPolicy:
        """Get security policies for user using your db_utils"""
        if not self.db_pool:
            logger.warning("No database pool - using default policies")
            return self._get_default_policies(user_id)
        
        try:
            # Use your db_utils pattern
            user_roles = await self._get_user_roles(user_id)
            rls_filters = await self._get_rls_policies(user_roles)
            cls_data = await self._get_cls_policies(user_roles)
            user_settings = await self._get_user_settings(user_id)
            
            return DatabaseSecurityPolicy(
                user_id=user_id,
                rls_filters=rls_filters,
                allowed_columns=cls_data['allowed_columns'],
                blocked_columns=cls_data['blocked_columns'],
                masked_columns=cls_data['masked_columns'],
                max_rows=user_settings['max_rows'],
                query_timeout=user_settings['query_timeout'],
                allowed_engines=user_settings['allowed_engines']
            )
            
        except Exception as e:
            logger.error(f"Failed to get user policies: {e}")
            return self._get_default_policies(user_id)
    
    async def _get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles using your db_utils"""
        query = """
            SELECT r.role_name 
            FROM security_user_roles ur
            JOIN security_roles r ON ur.role_id = r.role_id
            WHERE ur.user_id = $1
        """
        try:
            rows = await db_utils.fetch_all(self.db_pool, query, user_id)
            return [row['role_name'] for row in rows]
        except Exception as e:
            logger.warning(f"Failed to get user roles: {e}")
            return ['user']  # Default role
    
    async def _get_rls_policies(self, user_roles: List[str]) -> Dict[str, str]:
        """Get RLS policies using your db_utils"""
        if not user_roles:
            return {}
        
        query = """
            SELECT t.table_name, rp.filter_condition
            FROM security_rls_policies rp
            JOIN security_tables t ON rp.table_id = t.table_id
            JOIN security_roles r ON rp.role_id = r.role_id
            WHERE r.role_name = ANY($1) AND rp.is_active = TRUE
            ORDER BY rp.priority DESC
        """
        
        try:
            rows = await db_utils.fetch_all(self.db_pool, query, user_roles)
            
            rls_filters = {}
            for row in rows:
                table_name = row['table_name']
                condition = row['filter_condition']
                
                if table_name in rls_filters:
                    rls_filters[table_name] = f"({rls_filters[table_name]}) AND ({condition})"
                else:
                    rls_filters[table_name] = condition
            
            return rls_filters
            
        except Exception as e:
            logger.error(f"Failed to get RLS policies: {e}")
            return {}
    
    async def _get_cls_policies(self, user_roles: List[str]) -> Dict[str, Any]:
        """Get CLS policies using your db_utils"""
        if not user_roles:
            return {'allowed_columns': {}, 'blocked_columns': {}, 'masked_columns': {}}
        
        query = """
            SELECT 
                t.table_name,
                c.column_name,
                cp.access_type,
                cp.mask_type
            FROM security_cls_policies cp
            JOIN security_columns c ON cp.column_id = c.column_id
            JOIN security_tables t ON c.table_id = t.table_id
            JOIN security_roles r ON cp.role_id = r.role_id
            WHERE r.role_name = ANY($1) AND cp.is_active = TRUE
            ORDER BY t.table_name, c.column_name
        """
        
        try:
            rows = await db_utils.fetch_all(self.db_pool, query, user_roles)
            
            allowed_columns = {}
            blocked_columns = {}
            masked_columns = {}
            
            for row in rows:
                table_name = row['table_name']
                column_name = row['column_name']
                access_type = row['access_type']
                mask_type = row['mask_type']
                
                if access_type == 'allow':
                    allowed_columns.setdefault(table_name, []).append(column_name)
                elif access_type == 'deny':
                    blocked_columns.setdefault(table_name, []).append(column_name)
                elif access_type == 'mask' and mask_type:
                    masked_columns.setdefault(table_name, {})[column_name] = mask_type
            
            return {
                'allowed_columns': allowed_columns,
                'blocked_columns': blocked_columns,
                'masked_columns': masked_columns
            }
            
        except Exception as e:
            logger.error(f"Failed to get CLS policies: {e}")
            return {'allowed_columns': {}, 'blocked_columns': {}, 'masked_columns': {}}
    
    async def _get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user settings using your db_utils"""
        query = """
            SELECT max_rows_per_query, query_timeout_seconds, allowed_engines
            FROM security_user_settings 
            WHERE user_id = $1
        """
        
        try:
            row = await db_utils.fetch_one(self.db_pool, query, user_id)
            if row:
                return {
                    'max_rows': row['max_rows_per_query'],
                    'query_timeout': row['query_timeout_seconds'],
                    'allowed_engines': [DataEngine(engine) for engine in row['allowed_engines']]
                }
        except Exception as e:
            logger.warning(f"Failed to get user settings: {e}")
        
        # Return defaults
        return {
            'max_rows': 1000,
            'query_timeout': 30,
            'allowed_engines': [DataEngine.DRUID, DataEngine.POSTGRES, DataEngine.MYSQL]
        }
    
    def _get_default_policies(self, user_id: str) -> DatabaseSecurityPolicy:
        """Return default policies when database is unavailable"""
        return DatabaseSecurityPolicy(
            user_id=user_id,
            rls_filters={},
            allowed_columns={},
            blocked_columns={},
            masked_columns={},
            max_rows=1000,
            query_timeout=30,
            allowed_engines=[DataEngine.DRUID, DataEngine.POSTGRES, DataEngine.MYSQL]
        )
