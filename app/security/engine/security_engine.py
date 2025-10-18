from typing import Dict, Any, List, Optional
import asyncpg
import redis.asyncio as redis
import time
import logging

from app.config import Settings
from app.security.auth.identity import UserContext
from app.security.policies.policy_manager import PolicyManager, SecurityPolicy, QueryRequest, QueryResponse
from app.security.sql.sql_rewriter import SQLRewriter
from app.security.policies.row_level.rls_engine import RlsEngine
from app.security.policies.column_level.cls_engine import ClsEngine
from app.database.models import log_audit_event
from app.engines.connectors import QueryOrchestrator

logger = logging.getLogger(__name__)

class SecurityEngine:
    def __init__(self, db_pool: asyncpg.Pool, redis_client: redis.Redis):
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.settings = Settings()
        
        # Initialize components
        self.policy_manager = PolicyManager(db_pool, redis_client)
        self.sql_rewriter = SQLRewriter()
        self.rls_engine = RlsEngine()
        self.cls_engine = ClsEngine()
        self.query_orchestrator = QueryOrchestrator()
    
    async def authorize_query(self, user_context: UserContext, sql: str) -> bool:
        """Authorize if user can execute this query"""
        if not user_context.has_permission("data.query"):
            logger.warning(f"User {user_context.user_id} lacks data.query permission")
            return False
        
        return True
    
    async def execute_secure_query(
        self, 
        query_request: QueryRequest, 
        user_context: UserContext,
        source_ip: str = "unknown"
    ) -> QueryResponse:
        """Main method to execute query with security enforcement"""
        start_time = time.time()
        
        try:
            # Step 1: Authorization check
            if not await self.authorize_query(user_context, query_request.sql):
                raise PermissionError("User not authorized to execute queries")
            
            # Step 2: Get user security policies
            policies = await self.policy_manager.get_user_policies(user_context.user_id)
            
            # Step 3: Validate table access
            validation_errors = await self._validate_table_access(query_request.sql, user_context.user_id)
            if validation_errors:
                raise PermissionError(f"Table access denied: {', '.join(validation_errors)}")
            
            # Step 4: Rewrite SQL with security policies
            secure_sql, warnings = self.sql_rewriter.rewrite_sql(
                sql=query_request.sql,
                rls_filters=policies.rls_filters,
                allowed_columns=policies.allowed_columns,
                dialect=query_request.dialect
            )
            
            # Step 5: Execute query
            result = await self.query_orchestrator.execute_query(
                secure_sql, 
                user_context, 
                query_request.engine
            )
            
            # Step 6: Apply result-level security
            if policies.max_rows and len(result.get("data", [])) > policies.max_rows:
                result["data"] = result["data"][:policies.max_rows]
                result["truncated"] = True
                result["original_row_count"] = len(result["data"])
            
            execution_time = time.time() - start_time
            
            # Step 7: Audit logging
            await log_audit_event(
                self.db_pool,
                user_context.user_id,
                query_request.sql,
                secure_sql,
                execution_time,
                True,
                None,
                source_ip
            )
            
            return QueryResponse(
                original_sql=query_request.sql,
                secure_sql=secure_sql,
                result=result,
                execution_time=execution_time,
                engine_used=result.get("execution_engine", "unknown"),
                policies_applied=warnings
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log failed audit event
            await log_audit_event(
                self.db_pool,
                user_context.user_id,
                query_request.sql,
                "",
                execution_time,
                False,
                str(e),
                source_ip
            )
            
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def _validate_table_access(self, sql: str, user_id: str) -> List[str]:
        """Validate user has access to all tables in the query"""
        # Simplified implementation - in production, parse SQL properly
        errors = []
        try:
            import re
            tables = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
            tables += re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
            
            for table in set(tables):
                if not await self.policy_manager.validate_table_access(user_id, table):
                    errors.append(table)
        except Exception as e:
            logger.warning(f"Table validation error: {e}")
            
        return errors
    
    async def get_user_policies(self, user_id: str) -> SecurityPolicy:
        """Get security policies for user"""
        return await self.policy_manager.get_user_policies(user_id)
    
    async def update_user_policies(self, policy: SecurityPolicy) -> bool:
        """Update user security policies"""
        return await self.policy_manager.create_user_policy(policy)
    
    async def delete_user_policies(self, user_id: str) -> bool:
        """Delete user security policies"""
        return await self.policy_manager.delete_user_policy(user_id)
    
    @property
    def jwt_secret(self) -> str:
        """Get JWT secret"""
        return self.settings.jwt_secret