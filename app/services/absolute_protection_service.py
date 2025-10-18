#!/usr/bin/env python3
"""
Absolute protection service - ONLY developer can modify schema
Even database admins are blocked from security schema changes
"""

import logging
import os
from app.database.developer_lock import DeveloperSchemaLock
from app.utils.db_utils import execute_query

logger = logging.getLogger(__name__)

class AbsoluteProtectionService:
    """
    Implements absolute schema protection that cannot be bypassed
    """
    
    def __init__(self):
        self.developer_lock = DeveloperSchemaLock()
        self.initialized = False
    
    async def initialize_absolute_protection(self):
        """Initialize absolute protection system"""
        # Initialize developer lock
        await self.developer_lock.initialize_developer_lock()
        
        # Set developer signature in database session for trigger validation
        developer_sig = os.getenv('DEVELOPER_SCHEMA_SIGNATURE', self.developer_lock.developer_signature)
        await execute_query("SET universal_security.developer_signature = $1", developer_sig)
        
        # Install database triggers (one-time setup)
        await self._install_protection_triggers()
        
        self.initialized = True
        logger.info("🔐 Absolute schema protection initialized")
    
    async def _install_protection_triggers(self):
        """Install database-level protection triggers"""
        try:
            # Check if triggers already exist
            existing_trigger = await execute_query("""
                SELECT 1 FROM pg_event_trigger WHERE evtname = 'enforce_developer_ddl_authority'
            """)
            
            if not existing_trigger:
                # Install the protection triggers
                with open('sql/developer_lock_triggers.sql', 'r') as f:
                    trigger_sql = f.read()
                
                # Split and execute each command
                commands = [cmd.strip() for cmd in trigger_sql.split(';') if cmd.strip()]
                for command in commands:
                    if command and not command.startswith('--'):
                        await execute_query(command)
                
                logger.info("Database-level protection triggers installed")
            else:
                logger.info("Database-level protection triggers already installed")
                
        except Exception as e:
            logger.warning(f"Could not install database triggers (may require superuser): {e}")
            logger.info("Application-level protection is still active")
    
    async def enforce_absolute_protection(self):
        """Enforce absolute schema protection - called at application startup"""
        if not self.initialized:
            await self.initialize_absolute_protection()
        
        # Verify developer lock
        lock_status = await self.developer_lock.get_lock_status()
        
        if not lock_status['is_locked']:
            raise Exception("ABSOLUTE_PROTECTION_ERROR: Developer lock not active")
        
        if not lock_status['is_consistent']:
            if lock_status['developer_authority']:
                # Developer made changes - update lock
                await self.developer_lock.enforce_schema_lock()
                logger.info("Developer changes detected and lock updated")
            else:
                logger.critical("🚨 UNAUTHORIZED SCHEMA MODIFICATION BY NON-DEVELOPER!")
                logger.critical(f"Expected: {lock_status['locked_checksum']}")
                logger.critical(f"Current:  {lock_status['current_checksum']}")
                raise Exception("SECURITY BREACH: Schema modified without developer authority")
        
        logger.info("🔐 Absolute schema protection enforced successfully")
        return True
    
    async def developer_execute_ddl(self, ddl_sql: str, description: str = "Developer DDL"):
        """
        ONLY method for developer to execute DDL statements
        Requires proper developer authorization
        """
        if not self.initialized:
            await self.initialize_absolute_protection()
        
        # Set developer signature for trigger validation
        developer_sig = os.getenv('DEVELOPER_SCHEMA_SIGNATURE', self.developer_lock.developer_signature)
        await execute_query("SET universal_security.developer_signature = $1", developer_sig)
        
        # Execute through developer lock
        return await self.developer_lock.developer_schema_change(description, ddl_sql)
    
    async def get_absolute_protection_status(self):
        """Get comprehensive protection status"""
        lock_status = await self.developer_lock.get_lock_status()
        
        # Check trigger status
        trigger_status = await execute_query("""
            SELECT 
                EXISTS(SELECT 1 FROM pg_event_trigger WHERE evtname = 'enforce_developer_ddl_authority') as ddl_trigger_active,
                EXISTS(SELECT 1 FROM pg_event_trigger WHERE evtname = 'enforce_developer_drop_authority') as drop_trigger_active
        """)
        
        trigger_info = trigger_status[0] if trigger_status else {}
        
        return {
            "absolute_protection": True,
            "developer_lock": lock_status,
            "database_triggers": {
                "ddl_protection": trigger_info.get('ddl_trigger_active', False),
                "drop_protection": trigger_info.get('drop_trigger_active', False)
            },
            "protection_level": "ABSOLUTE" if lock_status['developer_authority'] else "COMPROMISED",
            "recommendation": "SECURE" if lock_status['is_consistent'] and lock_status['developer_authority'] else "IMMEDIATE_ACTION_REQUIRED"
        }
