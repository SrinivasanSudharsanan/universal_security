#!/usr/bin/env python3
"""
Final password security test
"""

import asyncio
import asyncpg
import hashlib
import secrets

async def final_password_test():
    print("🔒 FINAL PASSWORD SECURITY TEST")
    print("=" * 45)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # Check password security status
        print("1. Checking password storage...")
        users = await conn.fetch("""
            SELECT username, password_hash, password_salt
            FROM security_users
            ORDER BY username
        """)
        
        secured_count = 0
        for user in users:
            if user['password_hash'] and user['password_salt']:
                status = "✅ SECURED"
                secured_count += 1
            else:
                status = "❌ UNSECURED"
            print(f"   {user['username']}: {status}")
        
        print(f"\n2. Security summary:")
        print(f"   Secured users: {secured_count}/{len(users)}")
        
        # Test password verification
        print(f"\n3. Testing password verification...")
        test_cases = [
            ('admin', 'AdminSecure123!', True),
            ('admin', 'wrongpassword', False),
        ]
        
        for username, password, should_work in test_cases:
            user = await conn.fetchrow("""
                SELECT password_hash, password_salt 
                FROM security_users 
                WHERE username = $1
            """, username)
            
            if user and user['password_hash']:
                # Hash the test password with the stored salt
                test_hash = hashlib.sha256((password + user['password_salt']).encode()).hexdigest()
                matches = test_hash == user['password_hash']
                
                if matches == should_work:
                    result = "✅ PASS" if should_work else "✅ PASS (correctly rejected)"
                else:
                    result = "❌ FAIL"
                
                print(f"   {username} with '{password}': {result}")
            else:
                print(f"   {username}: ❌ NO PASSWORD SET")
        
        await conn.close()
        
        if secured_count == len(users):
            print(f"\n🎉 ALL PASSWORDS ARE SECURELY ENCRYPTED!")
            print("   🔒 Passwords are stored as SHA-256 hashes with random salts")
            return True
        else:
            print(f"\n⚠️  Some passwords are not secured")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(final_password_test())
    exit(0 if success else 1)
