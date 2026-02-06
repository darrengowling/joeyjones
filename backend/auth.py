"""
Authentication and Authorization Utilities
Provides JWT token management, magic link generation, and RBAC
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase

# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30
MAGIC_LINK_EXPIRE_MINUTES = 15

# Password hashing context (for future password auth)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_token(token: str) -> str:
    """Hash a token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_magic_token() -> str:
    """Generate a secure random magic link token"""
    return secrets.token_urlsafe(32)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload data to encode in token
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token"""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token to decode
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication token: {str(e)}"
        )


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token or X-User-ID header
    Supports both new JWT auth and legacy X-User-ID for backward compatibility
    
    Args:
        authorization: Bearer token from Authorization header
        x_user_id: Legacy user ID from X-User-ID header
    
    Returns:
        User data dictionary with id, email, role, isAdmin
    
    Raises:
        HTTPException: If authentication fails
    """
    from db_manager import get_db_manager
    db_manager = get_db_manager()
    db = db_manager.db
    
    user_id = None
    email = None
    role = "manager"
    
    # Try JWT authentication first
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format. Use: Bearer <token>"
            )
        
        token = authorization.replace("Bearer ", "")
        payload = decode_token(token)
        
        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "manager")
    
    # Fall back to legacy X-User-ID header for backward compatibility
    elif x_user_id:
        user_id = x_user_id
    
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide Authorization header or X-User-ID"
        )
    
    # Fetch user from database to get isAdmin flag
    user_data = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    return {
        "id": user_id,
        "email": email or (user_data.get("email") if user_data else None),
        "role": role,
        "isAdmin": user_data.get("isAdmin", False) if user_data else False
    }


async def require_commissioner(
    user: Dict[str, Any] = Depends(get_current_user),
    league_id: Optional[str] = None,
    db: Optional[AsyncIOMotorDatabase] = None
) -> Dict[str, Any]:
    """
    Verify that the current user is a commissioner of the specified league
    
    Args:
        user: Current authenticated user
        league_id: League ID to check commissioner status for
        db: Database instance
    
    Returns:
        User data if authorized
    
    Raises:
        HTTPException: If user is not the commissioner
    """
    if not league_id or not db:
        # If league_id or db not provided, just check if user has commissioner role
        if user.get("role") == "commissioner":
            return user
        raise HTTPException(
            status_code=403,
            detail="Commissioner role required"
        )
    
    # Check if user is commissioner of this specific league
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if league.get("commissionerId") != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the league commissioner can perform this action"
        )
    
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


class TokenBlacklist:
    """
    In-memory token blacklist (in production, use Redis)
    Stores revoked tokens until their expiration
    """
    def __init__(self):
        self._blacklist = set()
    
    def add(self, token: str):
        """Add token to blacklist"""
        self._blacklist.add(token)
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in self._blacklist
    
    def remove_expired(self):
        """Remove expired tokens from blacklist (called periodically)"""
        # In production with Redis, use TTL for automatic expiration
        pass


# Global token blacklist instance
token_blacklist = TokenBlacklist()
