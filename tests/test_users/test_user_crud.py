import pytest
from sqlalchemy.orm import Session

from app.exceptions.user_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.models.users import User
from app.users.schemas import UserCreate, UserUpdate
from app.users.utils import CRUDUser

crud_user = CRUDUser(User)


def test_get_all_users(db_session: Session, test_user, test_admin):
    users = crud_user.get_all_users(db_session)

    assert len(users) == 2
    assert any(user.email == test_user.email for user in users)
    assert any(user.email == test_admin.email for user in users)


def test_get_user_by_id(db_session: Session, test_user):
    retrieved_user = crud_user.get_user_by_id(db_session, test_user.id)

    assert retrieved_user is not None
    assert retrieved_user.id is not None
    assert retrieved_user.hashed_password is not None
    assert retrieved_user.email == test_user.email
    assert retrieved_user.role == test_user.role


def test_get_user_by_id_not_found(db_session: Session):
    with pytest.raises(UserNotFoundException) as ex:
        crud_user.get_user_by_id(db_session, 999)

    assert ex.value.status_code == 404
    assert ex.value.detail == "User with ID 999 not found."


@pytest.mark.asyncio
async def test_create_user(db_session: Session):
    user_data = UserCreate(email="test@example.com", role="polonus_manager")

    new_user = await crud_user.create_user(user_data, db_session)

    assert new_user is not None
    assert new_user.email == "test@example.com"
    assert new_user.role == "polonus_manager"


@pytest.mark.asyncio
async def test_create_duplicate_user(db_session: Session, test_user):
    user_data = UserCreate(email=test_user.email, role=test_user.role)

    with pytest.raises(UserAlreadyExistsException) as ex:
        await crud_user.create_user(user_data, db_session)

    assert ex.value.status_code == 400
    assert ex.value.detail == (f"User with email " f"{test_user.email} already exists.")


def test_update_user(db_session: Session, test_user):
    updates = UserUpdate(email="updated@example.com", role="polonus_manager")
    updated_user = crud_user.update_user(
        db_session, test_user.id, updates.model_dump(exclude_unset=True)
    )

    assert updated_user is not None
    assert updated_user.id == test_user.id
    assert updated_user.email == updates.email
    assert updated_user.role == updates.role


def test_delete_user(db_session: Session, test_user):
    assert test_user is not None

    crud_user.delete_user(db_session, test_user.id)

    with pytest.raises(UserNotFoundException) as ex:
        crud_user.get_user_by_id(db_session, test_user.id)

    assert ex.value.status_code == 404
    assert ex.value.detail == f"User with ID {test_user.id} not found."
