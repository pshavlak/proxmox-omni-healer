"""
Authentication and authorization utilities
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "config"))

try:
    from settings import SECRET_KEY, TOKEN_EXPIRE_MINUTES
except ImportError:
    SECRET_KEY = "change-this-to-a-random-secret-key"
    TOKEN_EXPIRE_MINUTES = 60

logger = logging.getLogger("omni_healer")
router = APIRouter()
security = HTTPBearer(auto_error=False)


# Simple token storage (in production, use Redis or database)
active_tokens = {}


def create_token(user: str) -> str:
    """Create a simple access token"""
    import secrets
    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "user": user,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    return token


def verify_token(token: str) -> Optional[dict]:
    """Verify token and return user info"""
    token_data = active_tokens.get(token)
    
    if not token_data:
        return None
    
    if datetime.utcnow() > token_data["expires_at"]:
        # Token expired
        del active_tokens[token]
        return None
    
    return token_data


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user = verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/login")
async def login(username: str, password: str):
    """Simple login endpoint (demo only - use proper auth in production)"""
    # In production, validate against Proxmox or LDAP
    if username and password:
        token = create_token(username)
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "expires_in": TOKEN_EXPIRE_MINUTES * 60
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout and invalidate token"""
    # Find and remove token
    token_to_remove = None
    for token, data in active_tokens.items():
        if data["user"] == current_user["user"]:
            token_to_remove = token
            break
    
    if token_to_remove:
        del active_tokens[token_to_remove]
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "success": True,
        "data": {
            "username": current_user["user"],
            "expires_at": current_user["expires_at"].isoformat()
        }
    }
