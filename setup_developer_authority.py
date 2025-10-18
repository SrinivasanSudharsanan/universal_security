#!/usr/bin/env python3
"""
Setup developer-exclusive authority with proper naming
"""

import asyncio
import sys
import os
import hashlib
import getpass
import socket

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.schema_protection_service import SchemaProtectionService

async def setup_developer_authority():
    """Setup developer-exclusive schema authority"""
    print("🔐 Setting Up Developer-Exclusive Schema Authority")
    print("=" * 60)
    
    # Generate or use existing developer signature
    developer_signature = os.getenv('DEVELOPER_SCHEMA_SIGNATURE')
    if not developer_signature:
        # Generate machine-specific signature
        machine_identifier = f"{socket.gethostname()}-{getpass.getuser()}-universal-security"
        developer_signature = hashlib.sha256(machine_identifier.encode()).hexdigest()
        print(f"🔑 Generated developer signature: {developer_signature[:16]}...")
        print("💡 Set DEVELOPER_SCHEMA_SIGNATURE environment variable for production")
    else:
        print(f"🔑 Using provided developer signature: {developer_signature[:16]}...")
    
    try:
        protection_service = SchemaProtectionService()
        
        print("\n1. Initializing protection system...")
        await protection_service.initialize_protection()
        print("   ✅ Protection system initialized")
        
        print("2. Establishing developer authority...")
        await protection_service.enforce_protection()
        print("   ✅ Developer authority established")
        
        print("3. Verifying exclusive control...")
        protection_status = await protection_service.get_protection_status()
        
        print(f"\n🎯 Developer Authority Status:")
        print("-" * 35)
        print(f"   Protection Level: {protection_status['protection_level']}")
        print(f"   Developer Authority: {protection_status['developer_lock']['developer_authority']}")
        print(f"   Schema Lock: {protection_status['developer_lock']['is_locked']}")
        
        if protection_status['protection_level'] == "DEVELOPER_EXCLUSIVE":
            print(f"\n🎉 Success: You have exclusive schema control!")
            print("   • Only you can modify security schema")
            print("   • All schema modifications require your authority")
            print("   • System is now developer-locked")
            
            # Save developer signature to backup file
            with open('.developer_authority.backup', 'w') as backup_file:
                backup_file.write(f"DEVELOPER_SCHEMA_SIGNATURE={developer_signature}\n")
                backup_file.write(f"# Generated for: {socket.gethostname()}-{getpass.getuser()}\n")
                backup_file.write(f"# Backup this file securely!\n")
            
            print(f"\n💾 Developer signature backed up to: .developer_authority.backup")
            print("   🔒 Keep this file secure - it's your schema authority key")
            
            return True
        else:
            print(f"\n⚠️  Setup incomplete - developer authority not confirmed")
            return False
            
    except Exception as error:
        print(f"❌ Developer authority setup failed: {error}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_developer_authority())
    if success:
        print(f"\n🚀 Next Step: Set environment variable for production:")
        print(f"   export DEVELOPER_SCHEMA_SIGNATURE='your_signature_here'")
    exit(0 if success else 1)
