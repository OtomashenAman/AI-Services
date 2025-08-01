# auth.py
import redis
import json
import logging
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.schemas.common_types import UserData
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Redis connection


# FastAPI security
security = HTTPBearer()

# Always validate with Django auth service
def get_auth_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserData:
    token = credentials.credentials

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(f"{settings.AUTH_URL}/auth/decode", json={"token": token}, headers=headers, timeout=5)
    except requests.RequestException as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Auth service error: {str(e)}")

    if res.status_code == 200:
        try:
            user = UserData(**res.json())
        except Exception as e:
            logger.error(f"Failed to parse user data: {res.json()}")
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user data format")
        
        logger.debug(f"[AUTH] Validated user: {user}")
        return user
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# Use Redis cache for token-based user lookup (only validate once per TTL)
def get_cached_auth_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserData:
    try:
        r =redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True,socket_connect_timeout=5,)  # Avoid long hangs
        token = credentials.credentials
        cached = r.get(token)
        if cached:
            logger.debug(f"[AUTH] Cache hit for token: {token[:10]}...")
            return UserData(**json.loads(cached))

        # Cache miss → validate with auth service
        user = get_auth_user(credentials)

        # Cache user for 15 minutes
        r.setex(token, 900, user.json())
        logger.debug(f"[AUTH] Cached user for token: {token[:10]}...")

        return user
    except Exception as e:
        logger.exception(f"[AUTH] Redis error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during Redis auth")

