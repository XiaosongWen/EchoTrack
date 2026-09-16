import uuid
from typing import Dict, Any, Optional
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from config import settings
from database import get_db
from models.user import User

security = HTTPBearer()

DEFAULT_FALLBACK_JWT_SECRET = "mock-supabase-jwt-secret-for-test-environments-32-bytes"

_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.supabase_url:
        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300)
    return _jwks_client


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify the JWT token from Supabase Auth and return the payload.
    Supports asymmetric algorithms (ES256, RS256) via Supabase JWKS,
    and symmetric algorithm (HS256) with SUPABASE_JWT_SECRET.
    The payload contains 'sub' (user UUID), 'email', 'role', etc.
    """
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as e:
        logger.warning(f"Failed to parse JWT header: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    alg = unverified_header.get("alg", "HS256")

    # If the token is signed with an asymmetric algorithm (e.g. ES256, RS256)
    if alg in ["ES256", "RS256", "ES384", "ES512", "RS384", "RS512"]:
        jwks_client = get_jwks_client()
        if jwks_client:
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[alg],
                    options={"verify_aud": False},
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )
            except Exception as e:
                logger.warning(f"JWKS verification failed for alg {alg}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
        else:
            logger.warning(f"No JWKS client available to verify {alg} token (SUPABASE_URL not configured)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    # Symmetric verification (HS256)
    secret = settings.supabase_jwt_secret or DEFAULT_FALLBACK_JWT_SECRET
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except (jwt.PyJWTError, Exception) as e:
        logger.warning(f"JWT decode failed: {e}")
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
