import random
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, Session, select

from . import mixin
from .base import (
    BaseSQLModel,
    RowId,
)

if TYPE_CHECKING:
    from .user import User

# region # API Keys for access ###################################################


# Shared properties
class ApiKeyBase(mixin.IsActive, mixin.Name, BaseSQLModel):
    user_id: RowId | None = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )


# Properties to receive via API on creation
class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyGenerate(mixin.IsActive, mixin.Name, BaseSQLModel):
    pass


# Properties to receive via API on creation
class ApiKeyUpdate(ApiKeyBase):
    pass


# Database model, database table inferred from class name
class ApiKey(mixin.RowId, ApiKeyBase, table=True):
    # --- database only items --------------------------------------------------
    api_key: str = Field(unique=True, nullable=False, max_length=64)

    # --- back_populates links -------------------------------------------------
    user: "User" = Relationship(back_populates="api_keys")

    # --- CRUD actions ---------------------------------------------------------
    @staticmethod
    def generate(size=30, chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789"):
        return "".join(random.choice(chars) for _ in range(size))

    @classmethod
    def create(cls, *, session: Session, create_obj: ApiKeyCreate) -> "ApiKey":
        data_obj = create_obj.model_dump(exclude_unset=True)

        # Generate new api key
        extra_data = {
            "api_key": ApiKey.generate(),
        }
        while True:
            extra_data["api_key"] = ApiKey.generate()
            statement = select(cls).where(cls.api_key == extra_data["api_key"])
            db_obj = session.exec(statement).first()
            if not db_obj:
                break

        db_obj = cls.model_validate(data_obj, update=extra_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(
        cls, *, session: Session, db_obj: "ApiKey", in_obj: ApiKeyUpdate
    ) -> "ApiKey":
        data_obj = in_obj.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def authenticate(cls, *, session: Session, api_key: str) -> "User | None":
        statement = select(cls).where(cls.api_key == api_key)
        db_obj = session.exec(statement).first()

        if not db_obj:
            return None
        elif not db_obj.is_active:
            return None
        elif not db_obj.user:
            return None
        return db_obj.user


# Properties to return via API, id is always required
class ApiKeyCreatedPublic(mixin.RowIdPublic, ApiKeyBase):
    api_key: str


# Properties to return via API, id is always required
class ApiKeyPublic(mixin.RowIdPublic, ApiKeyBase):
    pass


class ApiKeysPublic(BaseSQLModel):
    data: list[ApiKeyPublic]
    count: int


# endregion
