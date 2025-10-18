# app/database/init_db.py
import asyncpg
import logging

logger = logging.getLogger(__name__)

async def init_db(db_pool: asyncpg.Pool):
    """Initialize database - this just imports and calls the function from models.py"""
    from .models import init_db as init_db_schema
    await init_db_schema(db_pool)
    logger.info("Database initialized successfully")