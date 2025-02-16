from typing import List

from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.auth.utils import admin_only, get_current_user
from app.db import get_db
from app.models.users import User
from app.users.schemas import UserCreate, UserResponse, UserUpdate
from app.users.utils import CRUDUser

router = APIRouter()
crud_user = CRUDUser(User)


@router.get("/current", response_model=UserResponse)
def get_current_user_info(current_user_info: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user_info.id,
        email=current_user_info.email,
        role=current_user_info.role,
    )


@router.get("/list", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    return crud_user.get_all_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    return crud_user.get_user_by_id(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    user = crud_user.update_user(db, user_id, updates.model_dump(exclude_unset=True))
    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    request: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    return await crud_user.create_user(request, db)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    crud_user.delete_user(db, user_id)
    return {"message": f"User with ID {user_id} has been deleted."}
