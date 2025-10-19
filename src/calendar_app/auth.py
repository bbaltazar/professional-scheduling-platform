"""
Authentication and authorization utilities for the calendar application.

This module provides JWT token management, user authentication helpers,
and security dependencies for protecting API endpoints.
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

# Import settings
try:
    from .config import settings
    from .database import get_db
except ImportError:
    from config import settings
    from database import get_db

# JWT Configuration from settings
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_HOURS = settings.ACCESS_TOKEN_EXPIRE_HOURS

# Security
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Dictionary to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string to verify

    Returns:
        Decoded payload dict if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_specialist(request: Request, db: Session):
    """
    Get current authenticated specialist from session.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Specialist object if authenticated, None otherwise
    """
    # Import here to avoid circular imports
    try:
        from .database import Specialist, get_db
    except ImportError:
        from database import Specialist, get_db

    # Try to get token from cookie first
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = verify_token(token)
    if not payload:
        return None

    specialist_id = payload.get("specialist_id")
    if not specialist_id:
        return None

    # Fetch specialist with services eagerly loaded
    specialist = db.query(Specialist).filter(Specialist.id == specialist_id).first()
    return specialist


def require_authentication(request: Request, db: Session):
    """
    Dependency to require authentication.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Authenticated Specialist object

    Raises:
        HTTPException: If authentication fails
    """
    specialist = get_current_specialist(request, db)
    if not specialist:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to access professional features.",
        )
    return specialist


def get_current_specialist_dep(request: Request, db: Session = Depends(get_db)):
    """
    Dependency function for getting current authenticated specialist.
    Use this in FastAPI route dependencies with Depends().

    Args:
        request: FastAPI request object
        db: Database session (auto-injected by FastAPI)

    Returns:
        Specialist object if authenticated, None otherwise
    """
    return get_current_specialist(request, db)


def require_authentication_dep(request: Request, db: Session = Depends(get_db)):
    """
    Dependency function that requires authentication.
    Use this in FastAPI route dependencies with Depends().

    Args:
        request: FastAPI request object
        db: Database session (auto-injected by FastAPI)

    Returns:
        Authenticated Specialist object

    Raises:
        HTTPException: If authentication fails
    """
    return require_authentication(request, db)
