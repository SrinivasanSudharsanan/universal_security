#!/usr/bin/env python3
"""
Fix the CLS engine query to use the correct table structure
"""

import re

# Read the current CLS engine
with open('app/security/policies/column_level/cls_engine.py', 'r') as f:
    content = f.read()

# Find and replace the policy loading query
# Look for the query that loads policies
old_query_pattern = r"SELECT.*?FROM.*?column_policies.*?WHERE"

# Check if we can find the problematic query
if "cp.policy_id" in content:
    print("Found the problematic query with cp.policy_id")
    
    # Find the exact query
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "cp.policy_id" in line:
            print(f"Line {i}: {line}")
            
    # Let's replace the entire initialize_engine method
    new_method = '''
    async def initialize_engine(self):
        """Initialize the CLS engine by loading policies from database"""
        print("🔄 Initializing Universal CLS Engine...")
        
        try:
            # Query to load all active column-level security policies
            # USING THE CORRECT TABLE STRUCTURE
            query = """
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
            """
            
            policies_data = await self.execute_database_query(query)
            print(f"📊 Loaded {len(policies_data)} policies from database")
            
            # Organize policies by table -> column -> role
            self.policies = {}
            for policy in policies_data:
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
            total_policies = len(policies_data)
            print(f"✅ Universal CLS Engine initialized: {table_count} tables, {total_policies} policies")
            
        except Exception as e:
            print(f"❌ Failed to initialize CLS engine: {e}")
            logger.error(f"CLS engine initialization failed: {e}")
            raise
'''

    # Replace the initialize_engine method
    import re
    pattern = r"async def initialize_engine\(self\):.*?def \w+|\Z"
    new_content = re.sub(pattern, new_method + '\n\n    def ', content, flags=re.DOTALL)
    
    # Write the fixed content
    with open('app/security/policies/column_level/cls_engine.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed CLS engine query")
else:
    print("Could not find the problematic query pattern")
    print("Let me check the current initialize_engine method:")
    
    # Extract the current initialize_engine method
    match = re.search(r"async def initialize_engine\(self\):.*?def \w+", content, re.DOTALL)
    if match:
        print("Current initialize_engine method:")
        print(match.group(0))
