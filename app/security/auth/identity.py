from pydantic import BaseModel
from typing import List, Optional

class UserContext(BaseModel):
    """User identity and context"""
    user_id: str
    email: str
    roles: List[str]
    permissions: List[str]
    tenant_id: Optional[str] = None
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return "admin" in self.roles