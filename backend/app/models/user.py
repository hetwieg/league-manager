import random
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Session, Field, Relationship, select

from app.core.config import settings
from app.core.security import get_password_hash, verify_password

from .base import (
    BaseSQLModel,
)
from . import mixin


# region User ##################################################################


# Shared properties
class UserBase(
    mixin.UserName,
    mixin.Email,
    mixin.FullName,
    mixin.ScoutingId,
    mixin.IsActive,
    mixin.IsVerified,
    BaseSQLModel
):
    pass


# Properties to receive via API on creation
class UserCreate(mixin.Password, UserBase):
    pass


class UserRegister(mixin.Password, BaseSQLModel):
    email: EmailStr = Field(max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(mixin.EmailUpdate, mixin.PasswordUpdate, UserBase):
    pass


class UserUpdateMe(mixin.FullName, mixin.EmailUpdate, BaseSQLModel):
    pass


class UpdatePassword(BaseSQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(mixin.RowId, UserBase, table=True):
    # --- database only items --------------------------------------------------
    hashed_password: str

    # --- back_populates links -------------------------------------------------

    # --- many-to-many links ---------------------------------------------------

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: UserCreate) -> "User":
        data_obj = create_obj.model_dump(exclude_unset=True)

        extra_data = {"hashed_password": get_password_hash(create_obj.password)}

        db_obj = cls.model_validate(data_obj, update=extra_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(cls, *, session: Session, db_obj: "User", in_obj: UserUpdate) -> "User":
        data_obj = in_obj.model_dump(exclude_unset=True)

        extra_data = {}
        if "password" in data_obj:
            password = data_obj["password"]
            hashed_password = get_password_hash(password)
            extra_data["hashed_password"] = hashed_password

        db_obj.sqlmodel_update(data_obj, update=extra_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def get_by_email(cls, *, session: Session, email: str) -> "User | None":
        statement = select(cls).where(cls.email == email)
        db_obj = session.exec(statement).first()
        return db_obj

    @classmethod
    def authenticate(
        cls, *, session: Session, email: str, password: str
    ) -> "User | None":
        db_obj = cls.get_by_email(session=session, email=email)
        if not db_obj:
            return None
        if not verify_password(password, db_obj.hashed_password):
            return None
        return db_obj


# Properties to return via API, id is always required
class UserPublic(mixin.RowIdPublic, UserBase):
    pass


class UsersPublic(BaseSQLModel):
    data: list[UserPublic]
    count: int


# endregion
