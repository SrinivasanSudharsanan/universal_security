#!/usr/bin/env python3
"""
Test the fixed security service
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.security_service import SecurityService

async def test_fixed_service():
    print("Testing Fixed Security Service")
    print("=" * 35)
    
    try:
        # Test basic connection
        roles = await SecurityService.get_all_roles()
        print(f"✅ Connection test: {len(roles)} roles found")
        
        # Test user lookup
        admin = await SecurityService.get_user_by_username('admin')
        if admin:
            print(f"✅ User lookup: Found {admin['username']}")
            
            # Check if password is set
            if admin.get('password_hash'):
                print(f"✅ Password storage: Hashed password present")
            else:
                print(f"⚠️ Password storage: No password set")
        else:
            print(f"❌ User lookup: Admin not found")
        
        # Test data sources
        sources = await SecurityService.get_data_sources()
        print(f"✅ Data sources: {len(sources)} found")
        
        print("\n🎉 Security service is working!")
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_service())
    exit(0 if success else 1)
