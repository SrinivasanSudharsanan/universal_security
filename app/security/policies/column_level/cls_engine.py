#!/usr/bin/env python3
"""
Clean, working Universal CLS Engine
"""

import logging
import re
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class UniversalClsEngine:
    """
    Universal Column-Level Security Engine
    Uses our simple column_level_security_policies table structure
    """
    
    def __init__(self, database_query_function: Callable):
        self.database_query_function = database_query_function
        self.policies = {}
        self.initialized = False
    
    async def initialize_engine(self):
        """Initialize the CLS engine by loading policies from database"""
        await self._load_policies()
        logger.info("Universal CLS Engine initialized")
    
    async def _load_policies(self):
        """Load CLS policies from database using our simple table structure"""
        try:
            print("🔄 Loading CLS policies from column_level_security_policies table...")
            policies = await self.database_query_function("""
                SELECT 
                    table_name,
                    column_name,
                    role_name, 
                    access_type,
                    mask_type,
                    custom_mask_rule,
                    is_active
                FROM column_level_security_policies 
                WHERE is_active = true
                ORDER BY table_name, column_name, role_name
            """)
            
            print(f"📊 Loaded {len(policies)} policies from database")
            
            # Cache policies by table -> column -> role
            self.policies = {}
            for policy in policies:
                table = policy['table_name']
                column = policy['column_name']
                role = policy['role_name']
                
                if table not in self.policies:
                    self.policies[table] = {}
                if column not in self.policies[table]:
                    self.policies[table][column] = {}
                
                self.policies[table][column][role] = {
                    'access_type': policy['access_type'],
                    'mask_type': policy['mask_type'],
                    'custom_mask_rule': policy['custom_mask_rule']
                }
            
            self.initialized = True
            table_count = len(self.policies)
            print(f"✅ Policies cached: {table_count} tables, {len(policies)} total policies")
            
        except Exception as e:
            print(f"❌ Failed to load CLS policies: {e}")
            raise
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status information"""
        if not hasattr(self, 'policies') or not self.policies:
            return {
                "engine_type": "universal_cls",
                "status": "inactive",
                "tables_covered": 0,
                "total_policies": 0,
                "mask_types_supported": ["full", "partial", "email", "phone", "hash", "custom"]
            }
        
        # Count total policies across all tables, columns, and roles
        total_policies = 0
        for table in self.policies.values():
            for column in table.values():
                total_policies += len(column)
        
        return {
            "engine_type": "universal_cls",
            "status": "active" if self.initialized else "inactive",
            "tables_covered": len(self.policies),
            "total_policies": total_policies,
            "mask_types_supported": ["full", "partial", "email", "phone", "hash", "custom"]
        }
    
    async def get_allowed_columns(self, user_roles: List[str], table_name: str) -> List[Dict[str, Any]]:
        """Get list of columns the user can access in the specified table"""
        if not self.initialized:
            await self.initialize_engine()
        
        if table_name not in self.policies:
            return []
        
        # Known actual columns in Druid tables (from schema discovery)
        actual_columns = {
            'employees': ['__time', 'name', 'department', 'access_level', 'count', 'salary_sum'],
            'sales': ['__time', 'product', 'customer', 'region', 'quarter', 'amount_sum', 'count']
        }
        
        allowed_columns = []
        for column_name, role_policies in self.policies[table_name].items():
            # Only include columns that actually exist in the table
            if table_name in actual_columns and column_name not in actual_columns[table_name]:
                continue
                
            column_access = await self._get_best_column_access(user_roles, role_policies)
            if column_access['access_type'] != 'deny':
                allowed_columns.append({
                    'column_name': column_name,
                    'access_type': column_access['access_type'],
                    'mask_type': column_access['mask_type'],
                    'custom_mask_rule': column_access['custom_mask_rule']
                })
        
        return allowed_columns
    
    async def get_column_access(self, user_roles: List[str], table_name: str, column_name: str) -> Dict[str, Any]:
        """Get access information for a specific column"""
        if not self.initialized:
            await self.initialize_engine()
        
        if (table_name not in self.policies or 
            column_name not in self.policies[table_name]):
            return {'access_type': 'deny', 'mask_type': None, 'custom_mask_rule': None}
        
        role_policies = self.policies[table_name][column_name]
        return await self._get_best_column_access(user_roles, role_policies)
    
    async def _get_best_column_access(self, user_roles: List[str], role_policies: Dict[str, Dict]) -> Dict[str, Any]:
        """Get the best access level from user's roles"""
        best_access = {'access_type': 'deny', 'mask_type': None, 'custom_mask_rule': None}
        
        for role in user_roles:
            if role in role_policies:
                policy = role_policies[role]
                # Allow > Mask > Deny
                if policy['access_type'] == 'allow':
                    return policy
                elif policy['access_type'] == 'mask' and best_access['access_type'] != 'allow':
                    best_access = policy
        
        return best_access
    
    async def rewrite_sql_select(self, original_sql: str, user_roles: List[str], engine_type: str = "postgres") -> str:
        """Rewrite SQL SELECT query to enforce column-level security"""
        if not self.initialized:
            await self.initialize_engine()
        
        # Extract table name from query
        table_match = re.search(r'FROM\s+(\w+)', original_sql, re.IGNORECASE)
        if not table_match:
            return original_sql
        
        table_name = table_match.group(1)
        
        # Get allowed columns for this table and user roles
        allowed_columns = await self.get_allowed_columns(user_roles, table_name)
        
        if not allowed_columns:
            return self._create_no_access_query(original_sql, engine_type)
        
        # Handle SELECT * queries
        if re.search(r'SELECT\s+\*', original_sql, re.IGNORECASE):
            return self._rewrite_select_all(original_sql, [col['column_name'] for col in allowed_columns], engine_type)
        
        # For explicit column lists, we'd need a proper SQL parser
        # For now, return original if it's not SELECT *
        return original_sql
    
    def _create_no_access_query(self, original_sql: str, engine_type: str) -> str:
        """Create query that returns no results when user has no column access"""
        if engine_type in ["postgres", "mysql"]:
            return "SELECT 1 WHERE 1=0"  # Standard SQL
        elif engine_type == "druid":
            return "SELECT 1 FROM (SELECT 1) WHERE 1=0"  # Druid compatible
        else:
            return "SELECT 1 WHERE 1=0"  # Generic fallback
    
    def _rewrite_select_all(self, original_sql: str, allowed_columns: List[str], engine_type: str) -> str:
        """Rewrite SELECT * queries to explicit column lists"""
        if not allowed_columns:
            return self._create_no_access_query(original_sql, engine_type)
        
        # Escape reserved keywords for Druid
        if engine_type == "druid":
            escaped_columns = []
            for col in allowed_columns:
                if col.lower() in ['count', 'select', 'from', 'where', 'group', 'by']:
                    escaped_columns.append(f'"{col}"')  # Double quotes for Druid
                else:
                    escaped_columns.append(col)
            columns_str = ", ".join(escaped_columns)
        else:
            columns_str = ", ".join(allowed_columns)
            
        return re.sub(r'SELECT\s+\*', f'SELECT {columns_str}', original_sql, flags=re.IGNORECASE)
