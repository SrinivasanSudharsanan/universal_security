#!/usr/bin/env python3
"""
Test the security service
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.security_service import SecurityService

async def test_security_service():
    print("Testing Security Service")
    print("=" * 30)
    
    try:
        # Test 1: Get all roles
        print("1. Testing get_all_roles...")
        roles = await SecurityService.get_all_roles()
        print(f"   Found {len(roles)} roles: {[r['role_name'] for r in roles]}")
        
        # Test 2: Get user by username
        print("2. Testing get_user_by_username...")
        admin_user = await SecurityService.get_user_by_username('admin')
        if admin_user:
            print(f"   Found admin user: {admin_user['username']} ({admin_user['email']})")
        
        # Test 3: Get user roles
        print("3. Testing get_user_roles...")
        if admin_user:
            admin_roles = await SecurityService.get_user_roles(admin_user['user_id'])
            print(f"   Admin roles: {admin_roles}")
        
        # Test 4: Get data sources
        print("4. Testing get_data_sources...")
        data_sources = await SecurityService.get_data_sources()
        print(f"   Found {len(data_sources)} data sources:")
        for ds in data_sources:
            print(f"     - {ds['source_name']} ({ds['engine_type']})")
        
        # Test 5: Verify user access
        print("5. Testing verify_user_access...")
        admin_has_access = await SecurityService.verify_user_access('admin', 'admin')
        user1_has_access = await SecurityService.verify_user_access('user1', 'admin')
        print(f"   Admin has admin role: {admin_has_access}")
        print(f"   User1 has admin role: {user1_has_access}")
        
        print("\nAll security service tests passed!")
        return True
        
    except Exception as e:
        print(f"Security service test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_security_service())
    exit(0 if success else 1)
