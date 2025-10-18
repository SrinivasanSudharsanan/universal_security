#!/usr/bin/env python3
"""
Developer-exclusive schema modification lock
Prevents ANYONE (including admins) from changing security schema
"""

import logging
import hashlib
import os
from typing import Dict, Optional
from app.utils.db_utils import execute_query, fetch_one

logger = logging.getLogger(__name__)

class DeveloperSchemaLock:
    """
    Absolute schema lock that only allows changes from authorized developer
    Uses cryptographic signatures to enforce developer-only modifications
    """
    
    def __init__(self):
        self.lock_table = "developer_schema_lock"
        self.developer_signature = self._get_developer_signature()
        
    def _get_developer_signature(self) -> str:
        """Get developer cryptographic signature from environment"""
        dev_signature = os.getenv('DEVELOPER_SCHEMA_SIGNATURE')
        if not dev_signature:
            # Fallback: Generate from machine-specific identifiers
            import socket
            import getpass
            machine_id = f"{socket.gethostname()}-{getpass.getuser()}-universal-security"
            dev_signature = hashlib.sha256(machine_id.encode()).hexdigest()
            logger.warning("Using auto-generated developer signature - set DEVELOPER_SCHEMA_SIGNATURE for production")
        
        return dev_signature
    
    async def initialize_developer_lock(self):
        """Initialize the developer-exclusive lock system"""
        await execute_query(f"""
            CREATE TABLE IF NOT EXISTS {self.lock_table} (
                lock_id SERIAL PRIMARY KEY,
                developer_signature VARCHAR(64) UNIQUE NOT NULL,
                schema_checksum VARCHAR(64) NOT NULL,
                locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Insert initial lock if not exists
        existing_lock = await fetch_one(f"""
            SELECT * FROM {self.lock_table} WHERE is_active = TRUE
        """)
        
        if not existing_lock:
            initial_checksum = await self._calculate_schema_checksum()
            await execute_query(f"""
                INSERT INTO {self.lock_table} (developer_signature, schema_checksum)
                VALUES ($1, $2)
            """, self.developer_signature, initial_checksum)
            
            logger.info("🔐 Developer-exclusive schema lock initialized")
    
    async def _calculate_schema_checksum(self) -> str:
        """Calculate cryptographic checksum of entire security schema"""
        schema_info = await execute_query("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name LIKE 'security_%'
            ORDER BY table_name, ordinal_position
        """)
        
        schema_str = ""
        for row in schema_info:
            schema_str += f"{row['table_name']}.{row['column_name']}:{row['data_type']}:{row['is_nullable']}:{row['column_default']};"
        
        return hashlib.sha256(schema_str.encode()).hexdigest()
    
    async def verify_developer_authority(self, provided_signature: str = None) -> bool:
        """Verify that the request comes from authorized developer"""
        if provided_signature is None:
            provided_signature = self.developer_signature
        
        # Get the authorized developer signature from database
        authorized_lock = await fetch_one(f"""
            SELECT developer_signature FROM {self.lock_table} 
            WHERE is_active = TRUE ORDER BY locked_at DESC LIMIT 1
        """)
        
        if not authorized_lock:
            logger.error("No active developer lock found")
            return False
        
        # Cryptographic signature comparison
        import secrets
        is_authorized = secrets.compare_digest(
            provided_signature, 
            authorized_lock['developer_signature']
        )
        
        return is_authorized
    
    async def enforce_schema_lock(self):
        """Enforce developer-only schema modification"""
        current_checksum = await self._calculate_schema_checksum()
        locked_checksum = await fetch_one(f"""
            SELECT schema_checksum FROM {self.lock_table} 
            WHERE is_active = TRUE ORDER BY locked_at DESC LIMIT 1
        """)
        
        if not locked_checksum:
            raise Exception("Schema lock not initialized")
        
        # Check if schema has been modified without developer authorization
        if current_checksum != locked_checksum['schema_checksum']:
            # Verify if change was made by developer
            if not await self.verify_developer_authority():
                logger.critical("🚨 UNAUTHORIZED SCHEMA MODIFICATION DETECTED!")
                logger.critical("Schema was modified without developer authorization")
                raise Exception("SECURITY BREACH: Schema modified without developer authority")
            
            # Developer made the change - update the lock
            await self._update_developer_lock(current_checksum)
            logger.info("Developer-authorized schema change recorded")
    
    async def _update_developer_lock(self, new_checksum: str):
        """Update the developer lock with new schema checksum"""
        await execute_query(f"""
            UPDATE {self.lock_table} 
            SET schema_checksum = $1, locked_at = CURRENT_TIMESTAMP
            WHERE is_active = TRUE AND developer_signature = $2
        """, new_checksum, self.developer_signature)
    
    async def developer_schema_change(self, change_description: str, sql_script: str):
        """
        ONLY method to allow schema changes - requires developer authority
        """
        # Verify developer authority
        if not await self.verify_developer_authority():
            raise Exception("UNAUTHORIZED: Only designated developer can modify schema")
        
        # Verify current schema lock
        await self.enforce_schema_lock()
        
        # Calculate checksum of proposed change
        change_checksum = hashlib.sha256(sql_script.encode()).hexdigest()
        
        try:
            # Apply the schema change
            await execute_query(sql_script)
            
            # Update schema lock with new checksum
            new_schema_checksum = await self._calculate_schema_checksum()
            await self._update_developer_lock(new_schema_checksum)
            
            # Log the developer-authorized change
            await execute_query("""
                INSERT INTO security_schema_migrations 
                (version, description, checksum, applied_by)
                VALUES ($1, $2, $3, $4)
            """, "DEV_AUTHORIZED", change_description, change_checksum, "developer")
            
            logger.info(f"Developer-authorized schema change: {change_description}")
            return True
            
        except Exception as e:
            logger.error(f"Developer schema change failed: {e}")
            # Re-verify schema integrity after failed change
            await self.enforce_schema_lock()
            raise
    
    async def get_lock_status(self) -> Dict:
        """Get current developer lock status"""
        lock_info = await fetch_one(f"""
            SELECT developer_signature, schema_checksum, locked_at, is_active
            FROM {self.lock_table} 
            WHERE is_active = TRUE 
            ORDER BY locked_at DESC LIMIT 1
        """)
        
        current_checksum = await self._calculate_schema_checksum()
        is_locked = lock_info and lock_info['is_active']
        is_consistent = is_locked and (current_checksum == lock_info['schema_checksum'])
        
        return {
            "is_locked": is_locked,
            "is_consistent": is_consistent,
            "current_developer": lock_info['developer_signature'] if lock_info else None,
            "locked_checksum": lock_info['schema_checksum'] if lock_info else None,
            "current_checksum": current_checksum,
            "last_locked": lock_info['locked_at'] if lock_info else None,
            "developer_authority": await self.verify_developer_authority()
        }
