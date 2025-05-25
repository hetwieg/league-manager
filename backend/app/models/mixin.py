import uuid

from pydantic import EmailStr, BaseModel
from sqlmodel import Field

from .base import RowId as RowIdType


class Name(BaseModel):
    name: str | None = Field(default=None, nullable=False, unique=True, max_length=255)


class FullName(BaseModel):
    full_name: str | None = Field(default=None, nullable=True, max_length=255)


class IsActive(BaseModel):
    is_active: bool | None = Field(default=True, nullable=False)


class IsVerified(BaseModel):
    is_verified: bool | None = Field(default=False, nullable=False)


class UserName(BaseModel):
    username: str | None = Field(
        default=None, nullable=True, unique=True, max_length=255
    )


class Email(BaseModel):
    email: EmailStr | None = Field(
        default=None, nullable=True, unique=True, max_length=255
    )


class EmailUpdate(Email):
    email: EmailStr | None = Field(default=None, max_length=255)


class ScoutingId(BaseModel):
    scouting_id: str | None = Field(default=None, max_length=32)


class Password(BaseModel):
    password: str = Field(min_length=8, max_length=100)


class PasswordUpdate(Password):
    password: str | None = Field(default=None, min_length=8, max_length=40)


class RowId(BaseModel):
    id: RowIdType | None = Field(
        primary_key=True,
        nullable=False,
        default_factory=uuid.uuid4,
    )


class RowIdPublic(RowId):
    id: RowIdType


class Description(BaseModel):
    description: str | None = Field(default=None, nullable=True, max_length=512)
