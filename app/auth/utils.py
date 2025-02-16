from datetime import datetime, timezone
from typing import Type

from fastapi import Depends  # type: ignore
from fastapi.security.http import HTTPAuthorizationCredentials  # type: ignore
from jose import JWTError  # type: ignore
from redis import Redis  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.conf import http_bearer
from app.constants import settings
from app.db import get_db, get_redis
from app.exceptions.auth_exceptions import AdminAccessException
from app.exceptions.token_exceptions import (
    InvalidTokenException,
    TokenBlacklistedException,
)
from app.exceptions.user_exceptions import UserNotFoundException
from app.models.users import User
from app.users.schemas import UserResponse
from app.utils.auth import blacklist_token, get_payload, is_token_blacklisted

SECRET_KEY = settings.JWT_SECRET_KEY.get_secret_value()
ALGORITHM = settings.JWT_ALGORITHM


def logout_user(
    token_str: str, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)
):
    try:
        token = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_str)
        payload = get_payload(token)

        email: str = payload.get("sub")
        exp = payload.get("exp")

        get_user(db, email)
        success = blacklist_token(
            token.credentials, datetime.fromtimestamp(exp, tz=timezone.utc), redis
        )

        if success:
            return {"detail": "Logout successful"}

    except JWTError:
        return {"detail": "Token already invalid"}


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(http_bearer),
    redis: Redis = Depends(get_redis),
    db: Session = Depends(get_db),
) -> Type[User]:
    try:
        if is_token_blacklisted(token.credentials, redis):
            raise TokenBlacklistedException()

        payload = get_payload(token)
        email: str = payload.get("sub")
        if email is None:
            raise InvalidTokenException()

    except JWTError:
        raise InvalidTokenException()

    user = get_user(db, email)
    if user is None:
        raise UserNotFoundException(email=email)

    return user


def admin_only(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != "admin":
        raise AdminAccessException()

    return current_user


def get_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    raise UserNotFoundException(email=email)
