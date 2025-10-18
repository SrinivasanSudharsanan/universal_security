#!/usr/bin/env python3
"""
Universal Allowed Columns Manager
Manages column access permissions across all database types
"""

import logging
from typing import List, Dict, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)

class ColumnPermission(Enum):
    """Column permission levels"""
    READ = "read"
    WRITE = "write"
    NONE = "none"

class UniversalAllowedColumns:
    """
    Manages column-level access permissions universally
    """
    
    def __init__(self, database_query_function):
        self.database_query_function = database_query_function
        self.column_permissions = {}
        self.role_hierarchy = self._initialize_role_hierarchy()
    
    def _initialize_role_hierarchy(self) -> Dict[str, List[str]]:
        """Initialize role hierarchy for permission inheritance"""
        return {
            "admin": ["data_engineer", "business_analyst", "user"],
            "data_engineer": ["business_analyst", "user"],
            "business_analyst": ["user"],
            "user": []
        }
    
    async def initialize_permissions(self):
        """Initialize and load column permissions"""
        await self._load_column_permissions()
        logger.info("Universal Allowed Columns manager initialized")
    
    async def _load_column_permissions(self):
        """Load column permissions from database"""
        try:
            # Load base column permissions
            permissions = await self.database_query_function("""
                SELECT 
                    t.table_name,
                    c.column_name,
                    r.role_name,
                    cp.access_type,
                    cp.mask_type
                FROM security_cls_policies cp
                JOIN security_roles r ON cp.role_id = r.role_id
                JOIN security_columns c ON cp.column_id = c.column_id
                JOIN security_tables t ON c.table_id = t.table_id
                WHERE cp.is_active = true
                ORDER BY t.table_name, c.column_name, r.role_name
            """)
            
            # Organize permissions by table -> column -> role
            for perm in permissions:
                table = perm['table_name']
                column = perm['column_name']
                role = perm['role_name']
                
                if table not in self.column_permissions:
                    self.column_permissions[table] = {}
                if column not in self.column_permissions[table]:
                    self.column_permissions[table][column] = {}
                
                self.column_permissions[table][column][role] = {
                    'access_type': perm['access_type'],
                    'mask_type': perm['mask_type']
                }
            
            logger.info(f"Loaded permissions for {len(permissions)} column-role combinations")
            
        except Exception as e:
            logger.error(f"Failed to load column permissions: {e}")
            self.column_permissions = {}
    
    async def get_column_permission(
        self, 
        user_roles: List[str], 
        table_name: str, 
        column_name: str,
        operation: str = "read"
    ) -> ColumnPermission:
        """
        Get column permission level for user roles
        Supports role hierarchy and inheritance
        """
        if (table_name not in self.column_permissions or 
            column_name not in self.column_permissions[table_name]):
            # No specific policies - default to read access
            return ColumnPermission.READ
        
        column_roles = self.column_permissions[table_name][column_name]
        
        # Check each user role and inherited roles
        for user_role in user_roles:
            # Check direct role access
            if user_role in column_roles:
                access_type = column_roles[user_role]['access_type']
                if access_type == 'allow':
                    return ColumnPermission.READ
                elif access_type == 'deny':
                    return ColumnPermission.NONE
                elif access_type == 'mask':
                    return ColumnPermission.READ  # Can read masked data
            
            # Check inherited roles
            inherited_roles = self.role_hierarchy.get(user_role, [])
            for inherited_role in inherited_roles:
                if inherited_role in column_roles:
                    access_type = column_roles[inherited_role]['access_type']
                    if access_type == 'allow':
                        return ColumnPermission.READ
                    elif access_type == 'deny':
                        return ColumnPermission.NONE
                    elif access_type == 'mask':
                        return ColumnPermission.READ
        
        # Default to no access if no matching policies
        return ColumnPermission.NONE
    
    async def get_accessible_tables(self, user_roles: List[str]) -> List[str]:
        """Get list of tables accessible to user roles"""
        accessible_tables = set()
        
        for table_name, columns in self.column_permissions.items():
            for column_name, roles in columns.items():
                permission = await self.get_column_permission(user_roles, table_name, column_name)
                if permission != ColumnPermission.NONE:
                    accessible_tables.add(table_name)
                    break  # Only need one accessible column per table
        
        return list(accessible_tables)
    
    async def get_table_columns_summary(
        self, 
        user_roles: List[str], 
        table_name: str
    ) -> Dict[str, Any]:
        """
        Get summary of column permissions for a table
        """
        if table_name not in self.column_permissions:
            return {
                "table_name": table_name,
                "accessible_columns": 0,
                "total_columns": 0,
                "access_level": "none"
            }
        
        accessible_count = 0
        total_columns = len(self.column_permissions[table_name])
        
        for column_name in self.column_permissions[table_name]:
            permission = await self.get_column_permission(user_roles, table_name, column_name)
            if permission != ColumnPermission.NONE:
                accessible_count += 1
        
        # Determine overall table access level
        if accessible_count == 0:
            access_level = "none"
        elif accessible_count == total_columns:
            access_level = "full"
        else:
            access_level = "partial"
        
        return {
            "table_name": table_name,
            "accessible_columns": accessible_count,
            "total_columns": total_columns,
            "access_level": access_level,
            "access_percentage": round((accessible_count / total_columns) * 100, 2) if total_columns > 0 else 0
        }
    
    async def validate_query_access(
        self, 
        user_roles: List[str], 
        table_name: str, 
        requested_columns: List[str],
        operation: str = "read"
    ) -> Dict[str, Any]:
        """
        Validate if user can access all requested columns in a query
        """
        accessible_columns = []
        denied_columns = []
        
        for column in requested_columns:
            permission = await self.get_column_permission(user_roles, table_name, column, operation)
            if permission != ColumnPermission.NONE:
                accessible_columns.append(column)
            else:
                denied_columns.append(column)
        
        return {
            "is_allowed": len(denied_columns) == 0,
            "accessible_columns": accessible_columns,
            "denied_columns": denied_columns,
            "accessible_count": len(accessible_columns),
            "denied_count": len(denied_columns)
        }
    
    def get_permission_summary(self) -> Dict[str, Any]:
        """Get summary of loaded permissions"""
        total_tables = len(self.column_permissions)
        total_columns = 0
        total_policies = 0
        
        for table_columns in self.column_permissions.values():
            total_columns += len(table_columns)
            for column_roles in table_columns.values():
                total_policies += len(column_roles)
        
        return {
            "manager_type": "universal_allowed_columns",
            "total_tables": total_tables,
            "total_columns": total_columns,
            "total_policies": total_policies,
            "role_hierarchy": list(self.role_hierarchy.keys())
        }
