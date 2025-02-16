from fastapi import APIRouter, Depends, Request  # type: ignore
from redis import Redis  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.auth.schemas import Login, LogoutResponse, Token
from app.auth.utils import get_current_user, get_user, logout_user
from app.db import get_db, get_redis
from app.exceptions.auth_exceptions import InvalidCredentialsException
from app.users.schemas import UserResponse
from app.utils.auth import create_access_token, verify_password

router = APIRouter()


@router.post("/login", response_model=Token)
def login(request: Login, db: Session = Depends(get_db)):
    user = get_user(db, request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise InvalidCredentialsException
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=LogoutResponse)
def logout(
    http_request: Request,
    redis: Redis = Depends(get_redis),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):

    jwt_token = http_request.headers.get("Authorization").replace("Bearer ", "")
    response = logout_user(jwt_token, redis, db)

    return response
