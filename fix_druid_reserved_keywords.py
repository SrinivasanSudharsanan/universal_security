#!/usr/bin/env python3
"""
Fix Druid reserved keywords in CLS engine
"""

# Read the current CLS engine
with open('app/security/policies/column_level/cls_engine.py', 'r') as f:
    content = f.read()

# Druid reserved keywords that need escaping
druid_reserved_keywords = [
    'count', 'select', 'from', 'where', 'group', 'by', 'order', 'limit',
    'having', 'as', 'and', 'or', 'not', 'like', 'in', 'between', 'is', 'null',
    'true', 'false', 'case', 'when', 'then', 'else', 'end', 'join', 'inner',
    'left', 'right', 'outer', 'cross', 'union', 'all', 'distinct', 'cast'
]

# Find and replace the _rewrite_select_all method
old_method = '''    def _rewrite_select_all(self, original_sql: str, allowed_columns: List[str], engine_type: str) -> str:
        """Rewrite SELECT * queries to explicit column lists"""
        if not allowed_columns:
            return self._create_no_access_query(original_sql, engine_type)
        
        columns_str = ", ".join(allowed_columns)
        return re.sub(r'SELECT\s+\*', f'SELECT {columns_str}', original_sql, flags=re.IGNORECASE)'''

new_method = '''    def _rewrite_select_all(self, original_sql: str, allowed_columns: List[str], engine_type: str) -> str:
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
            
        return re.sub(r'SELECT\s+\*', f'SELECT {columns_str}', original_sql, flags=re.IGNORECASE)'''

# Replace the method
if old_method in content:
    content = content.replace(old_method, new_method)
    print("✅ Fixed Druid reserved keywords handling")
else:
    print("❌ Could not find _rewrite_select_all method to fix")

# Write the fixed content
with open('app/security/policies/column_level/cls_engine.py', 'w') as f:
    f.write(content)

print("✅ Druid reserved keywords fix applied")
