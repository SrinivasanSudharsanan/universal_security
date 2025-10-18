from typing import Dict, List, Optional, Any
import asyncpg
import redis.asyncio as redis
import json
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DataEngine(str, Enum):
    DRUID = "druid"
    ICEBERG = "iceberg"
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    FILES = "files"

class SQLDialect(str, Enum):
    MYSQL = "mysql"
    POSTGRES = "postgres"
    SNOWFLAKE = "snowflake"
    SPARK = "spark"

class QueryRequest(BaseModel):
    sql: str = Field(..., description="SQL query to execute")
    dialect: SQLDialect = Field(default=SQLDialect.MYSQL, description="SQL dialect")
    engine: Optional[DataEngine] = Field(None, description="Specific data engine to use")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Query parameters")

class QueryResponse(BaseModel):
    original_sql: str
    secure_sql: str
    result: Dict[str, Any]
    execution_time: float
    engine_used: DataEngine
    policies_applied: List[str]

class SecurityPolicy(BaseModel):
    user_id: str
    rls_filters: List[str] = Field(default_factory=list)
    allowed_columns: List[str] = Field(default_factory=list)
    denied_tables: List[str] = Field(default_factory=list)
    data_masks: Dict[str, str] = Field(default_factory=dict)
    max_rows: Optional[int] = Field(None, description="Maximum rows allowed to return")

class PolicyManager:
    def __init__(self, db_pool: asyncpg.Pool, redis_client: redis.Redis):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes
    
    async def get_user_policies(self, user_id: str) -> SecurityPolicy:
        """Get user security policies from cache or database"""
        cache_key = f"policies:{user_id}"
        
        try:
            # Try cache first
            cached = await self.redis_client.get(cache_key)
            if cached:
                policy_data = json.loads(cached)
                return SecurityPolicy(**policy_data)
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
        
        # Fetch from database with parameterized query
        async with self.db_pool.acquire() as conn:
            try:
                query = """
                    SELECT 
                        user_id,
                        COALESCE(rls_filters, '[]'::jsonb) as rls_filters,
                        COALESCE(allowed_columns, '[]'::jsonb) as allowed_columns,
                        COALESCE(denied_tables, '[]'::jsonb) as denied_tables,
                        COALESCE(data_masks, '{}'::jsonb) as data_masks,
                        max_rows
                    FROM user_security_policies 
                    WHERE user_id = $1 AND active = true
                """
                row = await conn.fetchrow(query, user_id)
                
                if row:
                    policy_data = {
                        "user_id": row["user_id"],
                        "rls_filters": row["rls_filters"],
                        "allowed_columns": row["allowed_columns"],
                        "denied_tables": row["denied_tables"],
                        "data_masks": row["data_masks"],
                        "max_rows": row["max_rows"]
                    }
                    
                    # Cache the result
                    try:
                        await self.redis_client.setex(
                            cache_key,
                            self.cache_ttl,
                            json.dumps(policy_data)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache policies: {e}")
                    
                    return SecurityPolicy(**policy_data)
                else:
                    # Return default policy if none found
                    return SecurityPolicy(user_id=user_id)
                    
            except Exception as e:
                logger.error(f"Database error fetching policies: {e}")
                return SecurityPolicy(user_id=user_id)
    
    async def validate_table_access(self, user_id: str, table_name: str) -> bool:
        """Check if user can access specific table"""
        policies = await self.get_user_policies(user_id)
        return table_name not in policies.denied_tables
    
    async def create_user_policy(self, policy: SecurityPolicy) -> bool:
        """Create or update user security policy"""
        async with self.db_pool.acquire() as conn:
            try:
                query = """
                    INSERT INTO user_security_policies 
                    (user_id, rls_filters, allowed_columns, denied_tables, data_masks, max_rows, active)
                    VALUES ($1, $2, $3, $4, $5, $6, true)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        rls_filters = EXCLUDED.rls_filters,
                        allowed_columns = EXCLUDED.allowed_columns,
                        denied_tables = EXCLUDED.denied_tables,
                        data_masks = EXCLUDED.data_masks,
                        max_rows = EXCLUDED.max_rows,
                        updated_at = CURRENT_TIMESTAMP
                """
                await conn.execute(
                    query,
                    policy.user_id,
                    policy.rls_filters,
                    policy.allowed_columns,
                    policy.denied_tables,
                    policy.data_masks,
                    policy.max_rows
                )
                
                # Invalidate cache
                cache_key = f"policies:{policy.user_id}"
                await self.redis_client.delete(cache_key)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to create user policy: {e}")
                return False
    
    async def delete_user_policy(self, user_id: str) -> bool:
        """Delete user security policy"""
        async with self.db_pool.acquire() as conn:
            try:
                query = "DELETE FROM user_security_policies WHERE user_id = $1"
                await conn.execute(query, user_id)
                
                # Invalidate cache
                cache_key = f"policies:{user_id}"
                await self.redis_client.delete(cache_key)
                
                return True
            except Exception as e:
                logger.error(f"Failed to delete user policy: {e}")
                return False