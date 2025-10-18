from fastapi import APIRouter, HTTPException
from typing import List

from app.security.policies.policy_manager import SecurityPolicy
from app.api.dependencies import SecurityEngineDep, CurrentUser, AdminUser

router = APIRouter()

@router.get("/policies/{user_id}", response_model=SecurityPolicy)
async def get_user_policies(
    user_id: str,
    user: CurrentUser,
    security_engine: SecurityEngineDep
):
    """Get security policies for user"""
    if user.user_id != user_id and "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return await security_engine.get_user_policies(user_id)

@router.put("/policies/{user_id}", response_model=dict)
async def update_user_policies(
    user_id: str,
    policy: SecurityPolicy,
    user: AdminUser,
    security_engine: SecurityEngineDep
):
    """Update security policies for user"""
    if policy.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    success = await security_engine.update_user_policies(policy)
    
    if success:
        return {"status": "success", "message": "Policies updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update policies")

@router.delete("/policies/{user_id}", response_model=dict)
async def delete_user_policies(
    user_id: str,
    user: AdminUser,
    security_engine: SecurityEngineDep
):
    """Delete security policies for user"""
    success = await security_engine.delete_user_policies(user_id)
    
    if success:
        return {"status": "success", "message": "Policies deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete policies")