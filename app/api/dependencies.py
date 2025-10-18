from fastapi import Depends, HTTPException, Request
from typing import Annotated

from app.security.auth.jwt_auth import authenticate_token
from app.security.engine.security_engine import SecurityEngine
from app.security.auth.identity import UserContext

async def get_security_engine(request: Request) -> SecurityEngine:
    """Dependency to get security engine"""
    return request.app.state.polylytics_app.security_engine

async def get_current_user(
    request: Request,
    security_engine: SecurityEngine = Depends(get_security_engine)
) -> UserContext:
    """Dependency to get current user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    user_context = await authenticate_token(token, security_engine.jwt_secret)
    
    if not user_context:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_context

async def require_admin(user: UserContext = Depends(get_current_user)) -> UserContext:
    """Dependency to require admin role"""
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# Type annotations for common dependencies
SecurityEngineDep = Annotated[SecurityEngine, Depends(get_security_engine)]
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
AdminUser = Annotated[UserContext, Depends(require_admin)]