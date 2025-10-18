# app/database/models.py
import asyncpg
from typing import Optional
from datetime import datetime
import json

async def init_db(db_pool: asyncpg.Pool):
    """Initialize database schema"""
    async with db_pool.acquire() as conn:
        # Create user security policies table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_security_policies (
                user_id TEXT PRIMARY KEY,
                rls_filters JSONB DEFAULT '[]',
                allowed_columns JSONB DEFAULT '[]',
                denied_tables JSONB DEFAULT '[]',
                data_masks JSONB DEFAULT '{}',
                max_rows INTEGER,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create audit logs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                original_sql TEXT NOT NULL,
                secure_sql TEXT,
                execution_time_ms INTEGER,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                source_ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create global security rules table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS global_security_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                condition TEXT NOT NULL,
                action TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)")

async def log_audit_event(
    db_pool: asyncpg.Pool,
    user_id: str,
    original_sql: str,
    secure_sql: str,
    execution_time: float,
    success: bool,
    error_message: Optional[str],
    source_ip: str
):
    """Log audit event to database"""
    async with db_pool.acquire() as conn:
        query = """
            INSERT INTO audit_logs 
            (user_id, original_sql, secure_sql, execution_time_ms, success, error_message, source_ip)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await conn.execute(
            query,
            user_id,
            original_sql,
            secure_sql,
            int(execution_time * 1000),  # Convert to milliseconds
            success,
            error_message,
            source_ip
        )

async def get_audit_logs(
    db_pool: asyncpg.Pool,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> list:
    """Get audit logs with flexible filtering"""
    async with db_pool.acquire() as conn:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        param_count = 0
        
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
        
        if start_date:
            param_count += 1
            query += f" AND created_at >= ${param_count}"
            params.append(start_date)
        
        if end_date:
            param_count += 1
            query += f" AND created_at <= ${param_count}"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC LIMIT $1"
        params.insert(0, limit)
        
        return await conn.fetch(query, *params)

async def get_user_policy(db_pool: asyncpg.Pool, user_id: str) -> Optional[dict]:
    """Get user security policy from database"""
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM user_security_policies WHERE user_id = $1 AND active = true",
            user_id
        )

async def create_user_policy(db_pool: asyncpg.Pool, policy_data: dict) -> bool:
    """Create or update user security policy"""
    async with db_pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO user_security_policies 
                (user_id, rls_filters, allowed_columns, denied_tables, data_masks, max_rows, active)
                VALUES ($1, $2, $3, $4, $5, $6, true)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    rls_filters = EXCLUDED.rls_filters,
                    allowed_columns = EXCLUDED.allowed_columns,
                    denied_tables = EXCLUDED.denied_tables,
                    data_masks = EXCLUDED.data_masks,
                    max_rows = EXCLUDED.max_rows,
                    updated_at = CURRENT_TIMESTAMP
            """,
            policy_data['user_id'],
            policy_data.get('rls_filters', []),
            policy_data.get('allowed_columns', []),
            policy_data.get('denied_tables', []),
            policy_data.get('data_masks', {}),
            policy_data.get('max_rows'))
            return True
        except Exception:
            return False