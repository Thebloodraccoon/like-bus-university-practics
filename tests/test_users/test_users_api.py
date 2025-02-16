from fastapi import status


def test_get_current_user_info(client, test_user, test_user_token):
    response = client.get(
        "/user/current",
        headers={"Authorization": f"Bearer {test_user_token.credentials}"},
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["email"] == test_user.email
    assert data["role"] == test_user.role


def test_get_all_users(client, test_admin_token, test_user):
    response = client.get(
        "/user/list",
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_200_OK

    users = response.json()
    assert len(users) >= 2
    assert all(isinstance(user["id"], int) for user in users)


def test_get_user_by_id(client, test_admin_token, test_admin):
    response = client.get(
        f"/user/{test_admin.id}/",
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_200_OK

    user = response.json()
    assert user["id"] == test_admin.id
    assert user["email"] == test_admin.email
    assert user["role"] == test_admin.role


def test_get_user_nonexistent_by_id(client, test_admin_token):
    response = client.get(
        "/user/999/",
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User with ID 999 not found."


def test_create_user(client, test_admin_token):
    new_user_data = {"email": "newuser@example.com", "role": "polonus_manager"}

    response = client.post(
        "/user/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] is not None
    assert data["email"] == new_user_data["email"]
    assert data["role"] == new_user_data["role"]


def test_create_user_duplicate(client, test_admin_token, test_user):
    new_user_data_duplicate = {"email": test_user.email, "role": test_user.role}

    response = client.post(
        "/user/",
        json=new_user_data_duplicate,
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == f"User with email {test_user.email} already exists."


def test_create_user_wrong_email(client, test_admin_token, test_user):
    new_user_data = {"email": "newusedcs", "role": "polonus_manager"}

    response = client.post(
        "/user/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["detail"] == "Invalid email"


def test_update_user_successes(client, test_admin_token, test_user):
    new_user_data = {"email": "update@gmail.com", "role": "admin"}

    response = client.put(
        f"/user/{test_user.id}/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == new_user_data["email"]
    assert data["role"] == new_user_data["role"]


def test_update_user_unsuccessful(client, test_admin_token, test_user):
    new_user_data = {"email": "update@gmail.com", "role": "admin"}

    response = client.put(
        "/user/999/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User with ID 999 not found."


def test_update_user_entity_error(client, test_admin_token, test_user):
    new_user_data = {"email": "update@gmail.com", "role": "admins"}

    response = client.put(
        f"/user/{test_user.id}/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_user_successes(client, test_admin_token, test_user):
    response = client.delete(
        f"/user/{test_user.id}/",
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["message"] == f"User with ID {test_user.id} has been deleted."
    )


def test_delete_user_unsuccessful(client, test_admin_token, test_user):
    wrong_id = test_user.id + 1000
    response = client.delete(
        f"/user/{wrong_id}/",
        headers={"Authorization": f"Bearer {test_admin_token.credentials}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"User with ID {wrong_id} not found."
