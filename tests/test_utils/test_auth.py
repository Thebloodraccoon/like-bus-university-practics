from datetime import datetime, timedelta, timezone

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.constants import settings
from app.utils.auth import (
    blacklist_token,
    create_access_token,
    get_password_hash,
    get_payload,
    is_token_blacklisted,
    verify_password,
)

SECRET_KEY = settings.JWT_SECRET_KEY.get_secret_value()
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def test_password_hashing():
    password = "testpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token_with_default_expiry():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "test@example.com"
    assert "exp" in payload

    expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    assert abs(
        datetime.fromtimestamp(payload["exp"], tz=timezone.utc) - expected_exp
    ) < timedelta(seconds=1)


def test_create_access_token_with_custom_expiry():
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(hours=1)
    token = create_access_token(data, expires_delta)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    expected_exp = datetime.now(timezone.utc) + expires_delta
    assert abs(
        datetime.fromtimestamp(payload["exp"], tz=timezone.utc) - expected_exp
    ) < timedelta(seconds=1)


def test_blacklist_token_success(redis_test):
    token = "test_token"
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=15)

    result = blacklist_token(token, expire_time, redis_test)

    assert result is True

    blacklist_key = f"blacklist:{token}"
    assert redis_test.exists(blacklist_key) == 1
    assert redis_test.get(blacklist_key) == "blacklisted"

    ttl = redis_test.ttl(blacklist_key)
    assert ttl > 0
    assert ttl <= 15 * 60


def test_blacklist_token_expired(redis_test):
    token = "expired_token"
    expire_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    result = blacklist_token(token, expire_time, redis_test)

    assert result is False
    assert redis_test.exists(f"blacklist:{token}") == 0


def test_is_token_blacklisted(redis_test):
    token = "test_token"
    blacklist_key = f"blacklist:{token}"

    assert not is_token_blacklisted(token, redis_test)

    redis_test.setex(blacklist_key, 300, "blacklisted")
    assert is_token_blacklisted(token, redis_test)


def test_is_token_blacklisted_expired(redis_test):
    token = "test_token"
    blacklist_key = f"blacklist:{token}"

    redis_test.setex(blacklist_key, 1, "blacklisted")

    import time

    time.sleep(1.1)

    assert not is_token_blacklisted(token, redis_test)


def test_get_payload_valid_token():
    data = {
        "sub": "test@example.com",
        "exp": datetime.now(timezone.utc).timestamp() + 3600,
    }
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    payload = get_payload(credentials)

    assert payload["sub"] == data["sub"]
    assert abs(payload["exp"] - data["exp"]) < 1


def test_get_payload_expired_token():
    data = {
        "sub": "test@example.com",
        "exp": datetime.now(timezone.utc).timestamp() - 3600,
    }
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(jwt.ExpiredSignatureError):
        get_payload(credentials)


def test_get_payload_invalid_token():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid_token"
    )

    with pytest.raises(jwt.JWTError):
        get_payload(credentials)


def test_get_payload_tampered_token():
    data = {
        "sub": "test@example.com",
        "exp": datetime.now(timezone.utc).timestamp() + 3600,
    }
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    tampered_token = token[:-1] + ("1" if token[-1] == "0" else "0")
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=tampered_token
    )

    with pytest.raises(jwt.JWTError):
        get_payload(credentials)
