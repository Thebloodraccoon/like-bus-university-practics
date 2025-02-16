from typing import Optional  # type: ignore

from fastapi import HTTPException, status  # type: ignore


class UserNotFoundException(HTTPException):
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None):
        detail = "User not found."

        if user_id:
            detail = f"User with ID {user_id} not found."

        if email:
            detail = f"User with email {email} not found."

        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsException(HTTPException):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {email} already exists.",
        )


class InvalidRoleException(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {message}"
        )
