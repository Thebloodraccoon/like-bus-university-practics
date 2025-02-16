import re

from pydantic import BaseModel, field_validator  # type: ignore

from app.exceptions.auth_exceptions import InvalidEmailException


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str


class Login(BaseModel):
    email: str
    password: str

    @field_validator("email")
    def validate_email(cls, email):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailException()

        return email


class LogoutResponse(BaseModel):
    detail: str
