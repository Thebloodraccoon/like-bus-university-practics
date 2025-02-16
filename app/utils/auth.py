from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import HTTPAuthorizationCredentials  # type: ignore
from jose import jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore
from redis import Redis  # type: ignore

from app.constants import settings

SECRET_KEY = settings.JWT_SECRET_KEY.get_secret_value()
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = (
        datetime.now(timezone.utc) + expires_delta
        if expires_delta
        else datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def blacklist_token(token: str, expire_time: datetime, redis: Redis):
    ttl = int((expire_time - datetime.now(timezone.utc)).total_seconds())
    if ttl > 0:
        redis.setex(f"blacklist:{token}", ttl, "blacklisted")
        return True

    return False


def is_token_blacklisted(token: str, redis: Redis):
    return redis.exists(f"blacklist:{token}")


def get_payload(token: HTTPAuthorizationCredentials):
    return jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
