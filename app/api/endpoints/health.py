from fastapi import APIRouter
from datetime import datetime

from app.api.dependencies import SecurityEngineDep
from app.main import polylytics_app

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "polylytics-security",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/deep")
async def deep_health_check(security_engine: SecurityEngineDep):
    """Deep health check including dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }
    
    # Check database connection
    try:
        async with polylytics_app.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["dependencies"]["database"] = "connected"
    except Exception as e:
        health_status["dependencies"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        await security_engine.redis_client.ping()
        health_status["dependencies"]["redis"] = "connected"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    health_status["dependencies"]["security_engine"] = "active"
    
    return health_status