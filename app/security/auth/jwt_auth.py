import jwt
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.security.auth.identity import UserContext

logger = logging.getLogger(__name__)

async def authenticate_token(token: str, jwt_secret: str) -> Optional[UserContext]:
    """Authenticate JWT token and extract user context"""
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        
        return UserContext(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            tenant_id=payload.get("tenant_id")
        )
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return None

def create_access_token(
    data: dict, 
    jwt_secret: str, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm="HS256")
    return encoded_jwt