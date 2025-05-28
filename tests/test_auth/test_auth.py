from fastapi import status
from jose import jwt

from app.constants import settings


def test_login_success(client, test_user_token):
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "testpassword123"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    response = client.post(
        "/auth/login", json={"email": test_user.email, "password": "wrongpassword"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_login_invalid_email_format(client):
    response = client.post(
        "/auth/login",
        json={"email": "invalid_email", "password": "password123"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid email"


def test_login_missing_fields(client):
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.post(
        "/auth/login",
        json={"password": "password123"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.post("/auth/login", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_token_contains_email(client, test_user):
    response = client.post(
        "/auth/login", json={"email": test_user.email, "password": "testpassword123"}
    )
    access_token = response.json()["access_token"]
    payload = jwt.decode(
        access_token,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert payload["sub"] == test_user.email


def test_logout_success(client, test_user, test_user_token):
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token.credentials}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Logout successful"


def test_logout_no_token(client):
    response = client.post("/auth/logout")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not authenticated"


def test_logout_invalid_token(client):
    response = client.post(
        "/auth/logout", headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"


def test_logout_already_logged_out(client, test_user_token, redis_test):
    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token.credentials}"},
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {test_user_token.credentials}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token has been blacklisted"
