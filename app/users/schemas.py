import re
from typing import Literal, Optional

from pydantic import EmailStr  # type: ignore
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.exceptions.auth_exceptions import InvalidEmailException


class UserBase(BaseModel):
    email: str
    role: Literal["admin", "polonus_manager", "dps_manager"]

    @field_validator("email")
    def validate_email(cls, email):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise InvalidEmailException()
        return email


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "polonus_manager", "dps_manager"]] = None
    id: Optional[int] = None

    @field_validator("id", mode="before")
    def validate_id(cls, value):
        if value is not None:
            raise ValueError("'id' field cannot be updated.")
        return value

    @model_validator(mode="before")
    def validate_data(cls, values):
        if not any(key for key in values if key != "id" and values[key] is not None):
            raise ValueError("At least one updatable field must be provided.")
        return values

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "updated_user@example.com", "role": "USER"}
        }
    )


class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
