import secrets
import string
from typing import Type

from sqlalchemy.orm import Session  # type: ignore

from app.exceptions.user_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.models.users import User
from app.users.schemas import UserCreate, UserResponse
from app.utils.auth import get_password_hash


def generate_random_password(length: int = 12) -> str:
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(secrets.choice(characters) for _ in range(length))


class CRUDUser:
    def __init__(self, model: Type[User]):
        self.model = model

    def get_all_users(self, db: Session) -> list[Type[User]]:
        return db.query(self.model).all()

    def get_user_by_id(self, db: Session, user_id: int) -> Type[User]:
        user = db.query(self.model).filter(self.model.id == user_id).first()
        if not user:
            raise UserNotFoundException(user_id)
        return user

    async def create_user(self, request: UserCreate, db: Session) -> UserResponse:
        existing_user = (
            db.query(self.model).filter(self.model.email == request.email).first()
        )
        if existing_user:
            raise UserAlreadyExistsException(request.email.__str__())

        password = generate_random_password()
        hashed_password = get_password_hash(password)

        new_user = self.model(
            email=request.email,
            hashed_password=hashed_password,
            role=request.role,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return UserResponse.model_validate(new_user)

    def update_user(self, db: Session, user_id: int, updates: dict) -> UserResponse:
        user = self.get_user_by_id(db, user_id)
        for field, value in updates.items():
            if hasattr(user, field):
                setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def delete_user(self, db: Session, user_id: int):
        user = self.get_user_by_id(db, user_id)
        db.delete(user)
        db.commit()
