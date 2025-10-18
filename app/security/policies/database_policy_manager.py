#!/usr/bin/env python3
"""
Database-driven Policy Manager - No hardcoded policies
Integrates with your existing policy_manager structure
"""

from typing import Dict, List, Any, Optional
import asyncpg
import redis.asyncio as redis
import logging
from dataclasses import dataclass

# Use your existing classes
from app.security.policies.policy_manager import DataEngine, SQLDialect
from .database_repository import DatabasePolicyRepository, DatabaseSecurityPolicy

logger = logging.getLogger(__name__)

@dataclass  
class QueryRequest:
    """Query execution request - matches your existing structure"""
    sql: str
    engine: DataEngine
    dialect: SQLDialect = SQLDialect.MYSQL

@dataclass
class QueryResponse:
    """Query execution response"""
    original_sql: str
    secure_sql: str
    result: Dict[str, Any]
    execution_time: float
    engine_used: DataEngine
    policies_applied: List[str]

class DatabasePolicyManager:
    """
    Database-driven policy manager that replaces hardcoded policies
    with dynamic database storage
    """
    
    def __init__(self, db_pool: asyncpg.Pool, redis_client: redis.Redis = None):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.repository = DatabasePolicyRepository(db_pool)
        self.cache_ttl = 300  # 5 minutes
    
    async def get_user_policies(self, user_id: str) -> DatabaseSecurityPolicy:
        """Get security policies from database with caching"""
        cache_key = f"security_policies:{user_id}"
        
        # Try cache first if Redis is available
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    # In production, use proper JSON serialization
                    # For now, we'll skip complex caching
                    pass
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        
        # Always get from database for fresh data
        policies = await self.repository.get_user_policies(user_id)
        
        # Cache the result
        if self.redis_client:
            try:
                # Simple cache - in production serialize properly
                await self.redis_client.setex(cache_key, self.cache_ttl, user_id)
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
        
        return policies
    
    async def validate_table_access(self, user_id: str, table_name: str) -> bool:
        """Validate if user can access table based on database policies"""
        policies = await self.get_user_policies(user_id)
        
        # Check if table is explicitly blocked
        if table_name in policies.blocked_columns:
            allowed_cols = policies.allowed_columns.get(table_name, [])
            return len(allowed_cols) > 0
        
        # If table has RLS filters or allowed columns, access is controlled but allowed
        if (table_name in policies.rls_filters or 
            table_name in policies.allowed_columns):
            return True
        
        # Default: allow access if no specific policies
        return True
    
    async def validate_engine_access(self, user_id: str, engine: DataEngine) -> bool:
        """Validate if user can use specific engine"""
        policies = await self.get_user_policies(user_id)
        return engine in policies.allowed_engines
    
    async def create_rls_policy(self, policy_data: Dict[str, Any]) -> bool:
        """Create new RLS policy in database"""
        success = await self.repository.create_rls_policy(policy_data)
        if success and self.redis_client:
            # Invalidate cache for affected users
            await self._invalidate_policy_cache()
        return success
    
    async def _invalidate_policy_cache(self):
        """Invalidate policy cache"""
        if self.redis_client:
            try:
                keys = await self.redis_client.keys("security_policies:*")
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info("Policy cache invalidated")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")
    
    async def get_policy_summary(self, user_id: str) -> Dict[str, Any]:
        """Get policy summary for user"""
        policies = await self.get_user_policies(user_id)
        
        return {
            'user_id': user_id,
            'rls_policies': len(policies.rls_filters),
            'tables_with_rls': list(policies.rls_filters.keys()),
            'column_policies': {
                'allowed_tables': list(policies.allowed_columns.keys()),
                'blocked_tables': list(policies.blocked_columns.keys()),
                'masked_columns': len(policies.masked_columns)
            },
            'limits': {
                'max_rows': policies.max_rows,
                'query_timeout': policies.query_timeout,
                'allowed_engines': [engine.value for engine in policies.allowed_engines]
            }
        }
