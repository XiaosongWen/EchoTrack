import uuid
from typing import Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.user import User

security = HTTPBearer()


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify the JWT token from Supabase Auth and return the payload.
    The payload contains 'sub' (user UUID), 'email', 'role', etc.
    """
    token = credentials.credentials
    try:
        # Supabase uses HS256 algorithm by default with SUPABASE_JWT_SECRET
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(
    payload: Dict[str, Any] = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Returns the User model from the database, auto-creating/syncing it if it doesn't exist.
    """
    user_sub = payload.get("sub")
    if not user_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID (sub) not found in token",
        )

    try:
        user_uuid = uuid.UUID(user_sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user UUID in token",
        )

    # Check if user already exists in DB
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if not user:
        email = payload.get("email")
        user_metadata = payload.get("user_metadata", {}) or {}
        username = user_metadata.get("user_name") or user_metadata.get("name")
        if not username and email:
            username = email.split("@")[0]

        user = User(
            id=user_uuid,
            email=email,
            username=username,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
