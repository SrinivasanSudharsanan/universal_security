#!/usr/bin/env python3
"""
Druid Connector with Integrated Column-Level Security
Secures Druid data using Universal CLS policies from PostgreSQL
"""

import logging
from typing import List, Dict, Any, Optional
from app.engines.druid_async_connector import AsyncDruidConnector
from app.security.policies.column_level.cls_engine import UniversalClsEngine
from app.utils.db_utils import DatabaseManager

logger = logging.getLogger(__name__)

class DruidClsConnector:
    """
    Druid connector with integrated Column-Level Security
    Applies CLS policies to all Druid queries automatically
    """
    
    def __init__(self):
        self.druid_connector = AsyncDruidConnector()
        self.cls_engine = None
        self.database_pool = None
        
    async def initialize(self, druid_config: Dict[str, Any] = None):
        """Initialize the CLS-secured Druid connector"""
        print("🔐 Initializing CLS-Secured Druid Connector")
        
        # Initialize database connection for CLS policies
        self.database_pool = await DatabaseManager.get_pool()
        
        # Create database query function for CLS engine
        async def execute_database_query(query_string, *query_parameters):
            async with self.database_pool.acquire() as connection:
                return await connection.fetch(query_string, *query_parameters)
        
        # Initialize CLS engine
        self.cls_engine = UniversalClsEngine(execute_database_query)
        await self.cls_engine.initialize_engine()
        
        # Initialize Druid connector
        await self.druid_connector.initialize(druid_config)
        
        logger.info("✅ CLS-secured Druid connector initialized")
    
    async def execute_secure_query(
        self, 
        query: str, 
        user_roles: List[str],
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Druid query with Column-Level Security applied
        """
        if not self.cls_engine:
            await self.initialize()
        
        # Step 1: Apply CLS to rewrite the query
        secured_query = await self.cls_engine.rewrite_sql_select(query, user_roles, "druid")
        
        logger.info(f"🔒 CLS Query Rewrite for roles {user_roles}:")
        logger.info(f"   Original: {query}")
        logger.info(f"   Secured:  {secured_query}")
        
        # Step 2: Execute the secured query against Druid
        try:
            results = await self.druid_connector.execute_query(secured_query)
            
            # Step 3: Apply additional masking if needed (for complex cases)
            masked_results = await self._apply_additional_masking(
                results, query, user_roles, secured_query
            )
            
            # Log the security event
            await self._log_security_event(user_id, user_roles, query, secured_query, len(masked_results))
            
            return masked_results
            
        except Exception as e:
            logger.error(f"❌ Secure Druid query failed: {e}")
            raise
    
    async def _apply_additional_masking(
        self, 
        results: List[Dict[str, Any]],
        original_query: str,
        user_roles: List[str],
        secured_query: str
    ) -> List[Dict[str, Any]]:
        """
        Apply additional data masking for complex scenarios
        This handles cases where SQL rewriting isn't sufficient
        """
        if not results:
            return results
        
        # Extract table name from query for policy lookup
        table_name = self._extract_table_name(original_query)
        if not table_name:
            return results
        
        masked_results = []
        
        for row in results:
            masked_row = {}
            for column_name, value in row.items():
                # Check CLS policy for this column
                access_info = await self.cls_engine.get_column_access(user_roles, table_name, column_name)
                
                if access_info['access_type'] == 'deny':
                    # Should not happen due to query rewriting, but safety check
                    continue
                elif access_info['access_type'] == 'mask' and access_info['mask_type']:
                    # Apply masking
                    from app.security.policies.column_level.column_masking import universal_masking_engine
                    masked_value = universal_masking_engine.mask_data(
                        value, access_info['mask_type'], access_info.get('custom_mask_rule')
                    )
                    masked_row[column_name] = masked_value
                else:
                    # Allow access
                    masked_row[column_name] = value
            
            masked_results.append(masked_row)
        
        return masked_results
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from SQL query"""
        import re
        # Simple table extraction - in production use proper SQL parser
        match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        return match.group(1) if match else None
    
    async def _log_security_event(
        self, 
        user_id: str, 
        user_roles: List[str],
        original_query: str,
        secured_query: str,
        result_count: int
    ):
        """Log security event for audit purposes"""
        try:
            async with self.database_pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO security_audit_log 
                    (user_id, user_roles, action_type, sql_query, secured_sql, result_count, success)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, user_id, user_roles, "CLS_SECURED_QUERY", original_query, secured_query, result_count, True)
        except Exception as e:
            logger.warning(f"Failed to log security event: {e}")
    
    async def get_secure_table_info(
        self, 
        user_roles: List[str],
        table_name: str = None
    ) -> Dict[str, Any]:
        """
        Get table information with CLS applied
        Shows only accessible columns for the user
        """
        if not self.cls_engine:
            await self.initialize()
        
        from app.security.policies.column_level.allowed_columns import UniversalAllowedColumns
        
        # Create allowed columns manager
        async def execute_database_query(query_string, *query_parameters):
            async with self.database_pool.acquire() as connection:
                return await connection.fetch(query_string, *query_parameters)
        
        allowed_manager = UniversalAllowedColumns(execute_database_query)
        await allowed_manager.initialize_permissions()
        
        if table_name:
            # Get specific table info
            table_info = await allowed_manager.get_table_columns_summary(user_roles, table_name)
            
            # Get allowed columns
            allowed_columns = await self.cls_engine.get_allowed_columns(user_roles, table_name)
            
            return {
                "table_name": table_name,
                "access_summary": table_info,
                "allowed_columns": allowed_columns,
                "accessible": table_info['access_level'] != 'none'
            }
        else:
            # Get all accessible tables
            accessible_tables = await allowed_manager.get_accessible_tables(user_roles)
            
            tables_info = []
            for table in accessible_tables:
                table_info = await allowed_manager.get_table_columns_summary(user_roles, table)
                tables_info.append({
                    "table_name": table,
                    "access_summary": table_info
                })
            
            return {
                "accessible_tables": tables_info,
                "total_tables": len(tables_info)
            }
    
    async def close(self):
        """Close connections"""
        if self.druid_connector:
            await self.druid_connector.close()
        if self.database_pool:
            await DatabaseManager.close_pool()
    
    def get_connector_status(self) -> Dict[str, Any]:
        """Get connector status information"""
        cls_status = self.cls_engine.get_engine_status() if self.cls_engine else {}
        
        return {
            "connector_type": "druid_cls_secured",
            "cls_engine_initialized": self.cls_engine is not None,
            "cls_status": cls_status,
            "druid_connected": self.druid_connector.is_connected if hasattr(self.druid_connector, 'is_connected') else False
        }
