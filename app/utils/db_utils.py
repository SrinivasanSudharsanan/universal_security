#!/usr/bin/env python3
"""
Database utilities for Universal Security Framework
"""

import asyncpg
import logging
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """PostgreSQL database connection manager"""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get database connection pool (singleton)"""
        if cls._pool is None:
            # Get PostgreSQL URL from environment variable
            postgres_url = os.getenv('POSTGRES_URL')
            if not postgres_url:
                # Fallback to direct connection if env var not set
                postgres_url = "postgresql://security_user:security_pass@localhost:5432/universal_security"
                
            try:
                cls._pool = await asyncpg.create_pool(
                    dsn=postgres_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("✅ PostgreSQL connection pool created")
            except Exception as e:
                logger.error(f"❌ Failed to create database pool: {e}")
                raise
        return cls._pool
    
    @classmethod
    async def close_pool(cls):
        """Close database connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("✅ PostgreSQL connection pool closed")

async def execute_query(query: str, *args) -> List[asyncpg.Record]:
    """Execute a query and return results"""
    pool = await DatabaseManager.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute_command(command: str, *args) -> str:
    """Execute a command (INSERT, UPDATE, DELETE)"""
    pool = await DatabaseManager.get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(command, *args)

async def fetch_one(query: str, *args) -> Optional[asyncpg.Record]:
    """Fetch a single row"""
    pool = await DatabaseManager.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)

async def fetch_all(query: str, *args) -> List[asyncpg.Record]:
    """Fetch all rows"""
    pool = await DatabaseManager.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def init_database():
    """Initialize database schema - verification only"""
    try:
        # Verify we can connect and query
        roles_count = await fetch_one("SELECT COUNT(*) as count FROM security_roles")
        logger.info(f"✅ Database verified with {roles_count['count']} security roles")
        return True
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False
