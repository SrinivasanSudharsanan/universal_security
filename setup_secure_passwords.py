#!/usr/bin/env python3
"""
Set secure passwords for existing users
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.security_service import SecurityService

async def setup_secure_passwords():
    print("🔐 Setting Up Secure Passwords")
    print("=" * 40)
    
    # Define secure passwords for each user
    user_passwords = {
        'admin': 'AdminSecure123!',
        'eng_manager': 'EngineerSecure456!',
        'business_user': 'BusinessSecure789!',
        'user1': 'UserSecure000!'
    }
    
    success_count = 0
    
    for username, password in user_passwords.items():
        try:
            success = await SecurityService.set_user_password(username, password)
            if success:
                print(f"✅ Password set for {username}")
                success_count += 1
            else:
                print(f"❌ Failed to set password for {username}")
        except Exception as e:
            print(f"❌ Error setting password for {username}: {e}")
    
    print(f"\n📊 Passwords set: {success_count}/{len(user_passwords)}")
    
    if success_count == len(user_passwords):
        print("🎉 All passwords secured successfully!")
        return True
    else:
        print("⚠️ Some passwords failed to set")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_secure_passwords())
    exit(0 if success else 1)
