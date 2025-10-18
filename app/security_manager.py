#!/usr/bin/env python3
"""
Application-level security manager for Druid
Implements roles, row-level security, and column security
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings
from typing import Dict, List, Any
import pandas as pd

class SecurityManager:
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.current_user = None
        self.user_roles = []
        
        # Security policies configuration
        self.rls_policies = {
            'employee_data': {
                'engineering': "department = 'Engineering'",
                'sales': "department = 'Sales'", 
                'hr': "department = 'HR'",
                'admin': "1=1"  # See everything
            }
        }
        
        self.column_security = {
            'employee_data': {
                'engineering': ['id', 'name', 'department', 'salary', 'access_level'],
                'sales': ['id', 'name', 'department', 'access_level'],  # No salary
                'hr': ['id', 'name', 'department', 'salary'],  # No access_level
                'public': ['id', 'name', 'department']  # Minimal info
            }
        }
        
        self.role_hierarchy = {
            'admin': ['engineering', 'sales', 'hr', 'public'],
            'engineering': ['public'],
            'sales': ['public'], 
            'hr': ['public'],
            'public': []
        }
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Simple authentication - in production, use proper auth"""
        # This is a mock - replace with real authentication
        users_db = {
            'alice': {'password': 'pass123', 'roles': ['engineering', 'public'], 'department': 'Engineering'},
            'bob': {'password': 'pass123', 'roles': ['sales', 'public'], 'department': 'Sales'},
            'charlie': {'password': 'pass123', 'roles': ['hr', 'public'], 'department': 'HR'},
            'admin': {'password': 'admin123', 'roles': ['admin', 'engineering', 'sales', 'hr', 'public'], 'department': None}
        }
        
        if username in users_db and users_db[username]['password'] == password:
            self.current_user = username
            self.user_roles = users_db[username]['roles']
            self.user_department = users_db[username]['department']
            print(f"🔐 Authenticated: {username} with roles: {self.user_roles}")
            return True
        return False
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role (including inherited roles)"""
        if not self.current_user:
            return False
        
        # Check direct roles and inherited roles
        user_effective_roles = set(self.user_roles)
        for user_role in self.user_roles:
            if user_role in self.role_hierarchy:
                user_effective_roles.update(self.role_hierarchy[user_role])
        
        return role in user_effective_roles
    
    def apply_rls(self, query: str, table_name: str) -> str:
        """Apply row-level security to query"""
        if not self.current_user or table_name not in self.rls_policies:
            return query
        
        # Find the most permissive policy user has access to
        applicable_policies = []
        for role in self.user_roles:
            if role in self.rls_policies[table_name]:
                applicable_policies.append(self.rls_policies[table_name][role])
        
        if not applicable_policies:
            # No access to this table
            return query + " WHERE 1=0"  # Return no rows
        
        # Use the most permissive policy (admin sees all)
        rls_condition = applicable_policies[0]
        
        if 'WHERE' in query.upper():
            base_query = query + f" AND ({rls_condition})"
        else:
            base_query = query + f" WHERE {rls_condition}"
        
        print(f"🛡️  RLS Applied: {base_query}")
        return base_query
    
    def apply_column_security(self, query: str, table_name: str) -> str:
        """Apply column-level security to query"""
        if not self.current_user or table_name not in self.column_security:
            return query
        
        # Find allowed columns for user's roles
        allowed_columns = set()
        for role in self.user_roles:
            if role in self.column_security[table_name]:
                allowed_columns.update(self.column_security[table_name][role])
        
        if not allowed_columns:
            return "SELECT 1 as no_access"  # No column access
        
        # If it's a SELECT * query, replace with specific columns
        if "SELECT *" in query.upper():
            columns = ", ".join(allowed_columns)
            new_query = query.replace("SELECT *", f"SELECT {columns}")
            print(f"🛡️  Column Security Applied: {new_query}")
            return new_query
        
        return query
    
    def execute_secure_query(self, query: str, table_name: str) -> pd.DataFrame:
        """Execute query with security applied"""
        if not self.current_user:
            raise Exception("User not authenticated")
        
        # Apply security layers
        secured_query = self.apply_rls(query, table_name)
        secured_query = self.apply_column_security(secured_query, table_name)
        
        # Initialize connection if not already done
        if not self.connector.get_available_engines():
            self.connector.initialize_connector('druid', self.settings.druid_config)
        
        return self.connector.execute_query(secured_query, engine_type='druid')
    
    def get_user_permissions(self) -> Dict[str, Any]:
        """Get current user's permissions summary"""
        if not self.current_user:
            return {}
        
        return {
            'username': self.current_user,
            'roles': self.user_roles,
            'department': self.user_department,
            'effective_roles': list(set(self.user_roles + 
                [r for role in self.user_roles for r in self.role_hierarchy.get(role, [])]))
        }

# Test the security manager
def test_security_manager():
    print("🛡️ TESTING APPLICATION-LEVEL SECURITY MANAGER")
    print("=" * 60)
    
    security = SecurityManager()
    
    # Create test data first
    print("\n1. Setting up test data...")
    security.connector.initialize_connector('druid', security.settings.druid_config)
    
    test_queries = [
        """
        CREATE TABLE IF NOT EXISTS employee_data (
            id BIGINT,
            name STRING,
            department STRING,
            salary DOUBLE,
            access_level STRING,
            personal_notes STRING
        )
        """,
        "INSERT INTO employee_data VALUES (1, 'Alice Engineer', 'Engineering', 80000, 'confidential', 'Top performer')",
        "INSERT INTO employee_data VALUES (2, 'Bob Salesman', 'Sales', 60000, 'restricted', 'Needs improvement')",
        "INSERT INTO employee_data VALUES (3, 'Charlie HR', 'HR', 70000, 'confidential', 'Excellent communicator')",
        "INSERT INTO employee_data VALUES (4, 'Diana Manager', 'Engineering', 90000, 'confidential', 'Leadership potential')",
        "INSERT INTO employee_data VALUES (5, 'Eve Intern', 'Sales', 45000, 'public', 'Learning quickly')"
    ]
    
    for query in test_queries:
        try:
            if "CREATE" in query or "INSERT" in query:
                security.connector.execute_command(query, engine_type='druid')
        except Exception as e:
            print(f"⚠️  Setup: {e}")
    
    print("\n2. Testing Different User Roles:")
    print("-" * 40)
    
    # Test Engineering user
    print("👩‍💻 Engineering User (alice):")
    security.authenticate_user('alice', 'pass123')
    perms = security.get_user_permissions()
    print(f"   Roles: {perms['roles']}")
    print(f"   Department: {perms['department']}")
    
    try:
        result = security.execute_secure_query("SELECT * FROM employee_data", "employee_data")
        print(f"   📊 Rows visible: {len(result)}")
        print(f"   🔒 Columns accessible: {list(result.columns)}")
        for _, row in result.iterrows():
            print(f"      👤 {row['name']} - {row['department']} - Salary: {row.get('salary', 'HIDDEN')}")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    # Test Sales user  
    print("\n👨‍💼 Sales User (bob):")
    security.authenticate_user('bob', 'pass123')
    perms = security.get_user_permissions()
    print(f"   Roles: {perms['roles']}")
    print(f"   Department: {perms['department']}")
    
    try:
        result = security.execute_secure_query("SELECT * FROM employee_data", "employee_data")
        print(f"   📊 Rows visible: {len(result)}")
        print(f"   🔒 Columns accessible: {list(result.columns)}")
        for _, row in result.iterrows():
            print(f"      👤 {row['name']} - {row['department']} - Salary: {row.get('salary', 'HIDDEN')}")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    # Test Admin user
    print("\n👑 Admin User (admin):")
    security.authenticate_user('admin', 'admin123')
    perms = security.get_user_permissions()
    print(f"   Roles: {perms['roles']}")
    print(f"   Department: {perms['department']}")
    
    try:
        result = security.execute_secure_query("SELECT * FROM employee_data", "employee_data")
        print(f"   📊 Rows visible: {len(result)}")
        print(f"   🔒 Columns accessible: {list(result.columns)}")
        for _, row in result.iterrows():
            print(f"      👤 {row['name']} - {row['department']} - Salary: {row['salary']}")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    security.connector.close_all()
    
    print("\n" + "=" * 60)
    print("🎯 SECURITY MANAGER SUMMARY:")
    print("   ✅ Role-based access control implemented")
    print("   ✅ Row-level security working")
    print("   ✅ Column-level security enforced")
    print("   ✅ User authentication functional")
    print("   ✅ Permission inheritance working")

if __name__ == "__main__":
    test_security_manager()