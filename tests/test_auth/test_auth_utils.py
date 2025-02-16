from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.auth.utils import admin_only, get_current_user, get_user, logout_user
from app.constants import settings
from app.exceptions.user_exceptions import UserNotFoundException


def test_logout_user_success(test_user, test_user_token, db_session, redis_test):
    result = logout_user(
        token_str=test_user_token.credentials, redis=redis_test, db=db_session
    )
    assert result is not None
    assert result == {"detail": "Logout successful"}


def test_logout_user_invalid_token(db_session, redis_test):
    result = logout_user(token_str="invalid_token", redis=redis_test, db=db_session)

    assert result == {"detail": "Token already invalid"}


def test_get_user_not_found(db_session):
    with pytest.raises(UserNotFoundException) as exc_info:
        get_user(db_session, "nonexistent@example.com")

    assert exc_info.value.status_code == 404
    assert "User with email nonexistent@example.com not found" in exc_info.value.detail


def test_get_current_user_user_not_found(db_session, redis_test):
    token = jwt.encode(
        {
            "sub": "nonexistent@example.com",
            "exp": datetime.now(timezone.utc).timestamp() + 3600,
        },
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    token_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(UserNotFoundException) as exc_info:
        get_current_user(token=token_credentials, db=db_session, redis=redis_test)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User with email nonexistent@example.com not found."


def test_get_current_user_valid_token(
    client, test_user, test_user_token, db_session, redis_test
):
    user = get_current_user(token=test_user_token, db=db_session, redis=redis_test)

    assert user.email == test_user.email
    assert user.id == test_user.id


def test_get_current_user_invalid_token(db_session, redis_test):
    invalid_token = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid_token"
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=invalid_token, db=db_session, redis=redis_test)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_expired_token(db_session, redis_test):
    expired_token = jwt.encode(
        {"sub": "test@example.com", "exp": 1},
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    expired_token_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=expired_token
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=expired_token_credentials, db=db_session, redis=redis_test
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_invalid_payload(db_session, redis_test):
    invalid_token = jwt.encode(
        {"wrong_field": "test@example.com"},
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )

    invalid_token_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=invalid_token
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=invalid_token_credentials, db=db_session, redis=redis_test
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_admin_only_with_admin_user(test_admin, redis_test):
    result = admin_only(test_admin)
    assert result == test_admin


def test_admin_only_with_regular_user(test_user):
    with pytest.raises(HTTPException) as exc_info:
        admin_only(test_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Only administrators have access to this endpoint"
