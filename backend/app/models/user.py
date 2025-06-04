import random
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Session, Field, Relationship, select

from app.core.config import settings
from app.core.security import get_password_hash, verify_password

from .base import (
    RowId,
    DocumentedStrEnum,
    DocumentedIntFlag,
    auto_enum,
    BaseSQLModel,
)
from . import mixin


# region User ##################################################################


class PermissionModule(DocumentedStrEnum):
    SYSTEM = auto_enum()
    USER = auto_enum()


class PermissionPart(DocumentedStrEnum):
    ADMIN = auto_enum()
    HEALTHCHECK = auto_enum()


class PermissionRight(DocumentedIntFlag):
    CREATE = auto_enum()
    READ = auto_enum()
    UPDATE = auto_enum()
    DELETE = auto_enum()

    ADMIN = CREATE | READ | UPDATE | DELETE


# #############################################################################
# link to User (many-to-many)
class UserRoleLink(BaseSQLModel, table=True):
    user_id: RowId | None = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    role_id: RowId | None = Field(
        default=None,
        foreign_key="role.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )


# #############################################################################


# Shared properties
class UserBase(
    mixin.UserName,
    mixin.Email,
    mixin.FullName,
    mixin.ScoutingId,
    mixin.IsActive,
    mixin.IsVerified,
    BaseSQLModel,
):
    pass


# Properties to receive via API on creation
class UserCreate(mixin.Password, UserBase):
    pass


class UserRegister(mixin.Password, mixin.FullName, BaseSQLModel):
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
    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)

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

    def add_role(self, *, name: str = None, id: RowId = None, db_obj: "Role" = None, session: Session) -> "User":
        db_obj = Role.get(name=name, id=id, db_obj=db_obj, session=session)

        to_add = next((add for add in self.roles if add == db_obj), None)

        if not to_add:
            self.roles.append(db_obj)
            session.commit()

        return self

    def remove_role(self, *, name: str = None, id: RowId = None, db_obj: "Role" = None, session: Session) -> "User":
        db_obj = Role.get(name=name, id=id, db_obj=db_obj, session=session)

        to_remove = next((remove for remove in self.roles if remove == db_obj), None)
        if to_remove:
            statement = select(UserRoleLink).where(
                    UserRoleLink.user_id == self.id,
                    UserRoleLink.role_id == db_obj.id
                )
            link_to_remove = session.exec(statement).first()

            if link_to_remove:
                session.delete(link_to_remove)
                session.commit()

        return self

    def has_permission(
        self,
        module: PermissionModule,
        part: PermissionPart,
        rights: PermissionRight | None = None,
    ) -> bool:
        return any(
            any(
                (
                    link.permission.module == module
                    and link.permission.part == part
                    and link.permission.is_active
                    and (not rights or (link.rights & rights) == rights)
                )
                for link in role.permission_links
                if role.is_active
            )
            for role in self.roles
        )


# Properties to return via API, id is always required
class UserPublic(mixin.RowIdPublic, UserBase):
    pass


class UsersPublic(BaseSQLModel):
    data: list[UserPublic]
    count: int


# endregion


# region Password manager ######################################################


# JSON payload containing access token
class Token(BaseSQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseSQLModel):
    sub: str | None = None


class NewPassword(BaseSQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# endregion


# region Permissions ###########################################################


# link to Roles (many-to-many)
class RolePermissionLink(BaseSQLModel, table=True):
    role_id: RowId | None = Field(
        default=None,
        foreign_key="role.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )
    permission_id: RowId | None = Field(
        default=None,
        foreign_key="permission.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )

    rights: "PermissionRight | None" = Field(default=0, nullable=False)

    role: "Role" = Relationship(back_populates="permission_links")
    permission: "Permission" = Relationship(back_populates="role_links")


# #############################################################################

# TODO: if we want to mange roles add all crud classes


class Role(
    mixin.RowId, mixin.Name, mixin.IsActive, mixin.Description, BaseSQLModel, table=True
):
    # --- database only items --------------------------------------------------

    # --- many-to-many links ---------------------------------------------------
    permission_links: list["RolePermissionLink"] = Relationship(back_populates="role")
    users: list["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: "Role") -> "Role":
        data_obj = create_obj.model_dump(exclude_unset=True)
        db_obj = cls.model_validate(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def get(cls, *, name: str = None, id: RowId = None, db_obj: "Role" = None, session: Session) -> "Role":
        if db_obj:
            pass
        elif name:
            db_obj = session.exec(select(Role).where(Role.name == name)).first()
        elif id:
            db_obj = session.exec(select(Role).where(Role.id == id)).first()

        return db_obj

    def add_permission(
        self, add: "Permission", *, session: Session, right: PermissionRight = None
    ) -> "Role":
        link = next(
            (link for link in self.permission_links if link.permission == add),
            None,
        )
        if link:
            link.rights = right
        else:
            self.permission_links.append(
                RolePermissionLink(
                    role=self,
                    permission=add,
                    rights=right,
                )
            )
            session.add(self.permission_links[-1])

        session.commit()

        return self

    def remove_permission(self, remove: "Permission", *, session: Session) -> "Role":
        link = next(
            (link for link in self.permission_links if link.permission == remove),
            None,
        )
        if link:
            session.delete(link)
            session.commit()

        return self


# #############################################################################


# All Permission will be generated during db init
class Permission(
    mixin.RowId, mixin.IsActive, mixin.Description, BaseSQLModel, table=True
):
    # --- database only items --------------------------------------------------
    module: PermissionModule = Field(nullable=False)
    part: PermissionPart = Field(nullable=False)

    # --- many-to-many links ---------------------------------------------------
    role_links: list["RolePermissionLink"] = Relationship(back_populates="permission")

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: "Permission") -> "Permission":
        data_obj = create_obj.model_dump(exclude_unset=True)
        db_obj = cls.model_validate(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj


# endregion
