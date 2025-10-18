from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from app.security.engine.security_engine import SecurityEngine
from app.security.auth.identity import UserContext
from app.api.dependencies import SecurityEngineDep, CurrentUser
from app.security.policies.policy_manager import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    request: Request,
    user: CurrentUser,
    security_engine: SecurityEngineDep
):
    """Execute SQL query with security enforcement"""
    try:
        source_ip = request.client.host if request.client else "unknown"
        
        response = await security_engine.execute_secure_query(
            query_request, user, source_ip
        )
        
        return response
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")