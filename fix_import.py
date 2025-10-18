#!/usr/bin/env python3
"""
Fix the import in __init__.py
"""

# Read the __init__.py file
with open('app/security/policies/column_level/__init__.py', 'r') as f:
    content = f.read()

# Replace ClsEngine with UniversalClsEngine
if 'from .cls_engine import ClsEngine' in content:
    content = content.replace('from .cls_engine import ClsEngine', 'from .cls_engine import UniversalClsEngine')
    print("✅ Fixed import in __init__.py")
elif 'UniversalClsEngine' not in content:
    # Add the import if it doesn't exist
    content = content + '\nfrom .cls_engine import UniversalClsEngine\n'
    print("✅ Added UniversalClsEngine import to __init__.py")
else:
    print("✅ Import already correct")

# Write the fixed content
with open('app/security/policies/column_level/__init__.py', 'w') as f:
    f.write(content)

print("✅ Import fix complete")
