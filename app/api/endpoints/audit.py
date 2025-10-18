from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime

from app.api.dependencies import AdminUser
from app.database.models import get_audit_logs
from app.main import polylytics_app

router = APIRouter()

@router.get("/audit/logs", response_model=List[dict])
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, description="Number of logs to return", ge=1, le=1000),
    user: AdminUser = None
):
    """Get audit logs (admin only)"""
    db_pool = polylytics_app.db_pool
    logs = await get_audit_logs(db_pool, user_id, start_date, end_date, limit)
    
    return [dict(log) for log in logs]