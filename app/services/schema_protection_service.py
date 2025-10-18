#!/usr/bin/env python3
"""
Schema protection service with proper naming conventions
Developer-exclusive schema modification control
"""

import logging
import os
from app.database.developer_schema_lock import DeveloperSchemaLock
from app.utils.db_utils import execute_query

logger = logging.getLogger(__name__)

class SchemaProtectionService:
    """
    Schema protection service implementing developer-exclusive control
    """
    
    def __init__(self):
        self.developer_lock = DeveloperSchemaLock()
        self.is_initialized = False
    
    async def initialize_protection(self):
        """Initialize schema protection system"""
        await self.developer_lock.initialize_developer_lock()
        self.is_initialized = True
        logger.info("Schema protection service initialized successfully")
    
    async def enforce_protection(self):
        """Enforce schema protection - called at application startup"""
        if not self.is_initialized:
            await self.initialize_protection()
        
        # Verify developer lock
        lock_status = await self.developer_lock.get_lock_status()
        
        if not lock_status['is_locked']:
            raise Exception("Schema protection error: Developer lock not active")
        
        if not lock_status['is_consistent']:
            if lock_status['developer_authority']:
                # Developer made changes - update lock
                await self.developer_lock.enforce_schema_lock()
                logger.info("Developer changes detected and lock updated")
            else:
                logger.critical("Unauthorized schema modification detected")
                logger.critical(f"Expected checksum: {lock_status['locked_checksum']}")
                logger.critical(f"Current checksum: {lock_status['current_checksum']}")
                raise Exception("Security breach: Schema modified without developer authority")
        
        logger.info("Schema protection enforced successfully")
        return True
    
    async def execute_developer_ddl(self, ddl_statement: str, description: str):
        """
        Execute DDL statement with developer authority verification
        """
        if not self.is_initialized:
            await self.initialize_protection()
        
        return await self.developer_lock.developer_execute_ddl(ddl_statement, description)
    
    async def get_protection_status(self):
        """Get comprehensive protection status"""
        lock_status = await self.developer_lock.get_lock_status()
        
        return {
            "protection_active": True,
            "developer_lock": lock_status,
            "protection_level": "DEVELOPER_EXCLUSIVE" if lock_status['developer_authority'] else "COMPROMISED",
            "security_status": "SECURE" if lock_status['is_consistent'] and lock_status['developer_authority'] else "COMPROMISED"
        }
