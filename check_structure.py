#!/usr/bin/env python3
"""
Check project folder structure
"""

import os
import sys

def get_project_structure():
    print("📁 UNIVERSAL SECURITY FRAMEWORK - PROJECT STRUCTURE")
    print("=" * 60)
    
    base_dir = "."
    
    # Define expected structure
    expected_structure = {
        "app/": "Main application package",
        "app/utils/": "Utility modules",
        "app/services/": "Business logic services",
        "sql/": "SQL schema files",
        "tests/": "Test files",
        "config/": "Configuration files"
    }
    
    print("🔍 CURRENT STRUCTURE:")
    print("-" * 40)
    
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        files = [f for f in files if not f.startswith('.') and not f.endswith('.pyc')]
        
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}📁 {os.path.basename(root)}/')
        
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py') or file in ['.env', 'requirements.txt', 'README.md']:
                print(f'{subindent}📄 {file}')
    
    print(f"\n📊 FILE COUNT BY TYPE:")
    print("-" * 40)
    
    file_types = {}
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith('.'):
                continue
            ext = os.path.splitext(file)[1]
            file_types[ext] = file_types.get(ext, 0) + 1
    
    for ext, count in sorted(file_types.items()):
        if ext:  # Skip files without extension
            print(f"   {ext or 'no ext'}: {count} files")
    
    # Check critical files
    print(f"\n✅ CRITICAL FILES CHECK:")
    print("-" * 40)
    
    critical_files = {
        '.env': 'Environment configuration',
        'app/__init__.py': 'App package init',
        'app/utils/__init__.py': 'Utils package init',
        'app/utils/db_utils.py': 'Database utilities',
        'app/utils/password_utils.py': 'Password utilities',
        'app/services/__init__.py': 'Services package init',
        'app/services/security_service.py': 'Security service',
    }
    
    missing_files = []
    for file, description in critical_files.items():
        if os.path.exists(file):
            print(f"   ✅ {file} - {description}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  MISSING FILES: {len(missing_files)}")
        for file in missing_files:
            print(f"   - {file}")
    else:
        print(f"\n🎉 ALL CRITICAL FILES PRESENT!")

if __name__ == "__main__":
    get_project_structure()
