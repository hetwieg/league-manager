from typing import TYPE_CHECKING

from sqlmodel import (
    Field,
    Relationship,
    Session,
    select,
)

from . import mixin
from .base import (
    BaseSQLModel,
    RowId,
)
from .user import (
    PermissionRight,
    User,
)

if TYPE_CHECKING:
    from .team import Team

# region # Event ###############################################################


# Shared properties
class EventUserLinkBase(BaseSQLModel):
    rights: PermissionRight = Field(default=PermissionRight.READ, nullable=False)


# Properties to receive via API on creation
class EventUserLinkCreate(EventUserLinkBase):
    user_id: RowId = Field(default=None, nullable=False)


# Properties to receive via API on update, all are optional
class EventUserLinkUpdate(EventUserLinkBase):
    pass


# Database model, database table inferred from class name
class EventUserLink(EventUserLinkBase, table=True):
    event_id: RowId = Field(
        foreign_key="event.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )

    user_id: RowId = Field(
        foreign_key="user.id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )


    event: "Event" = Relationship(back_populates="user_links")
    user: "User" = Relationship(back_populates="event_links")


# Properties to return via API
class EventUserLinkPublic(EventUserLinkBase):
    user_id: RowId
    event_id: RowId


class EventUserLinksPublic(BaseSQLModel):
    data: list[EventUserLinkPublic]
    count: int


# ##############################################################################


# Shared properties
class EventBase(
    mixin.Name,
    mixin.Contact,
    mixin.StartEndDate,
    mixin.IsActive,
    BaseSQLModel,
):
    pass


# Properties to receive via API on creation
class EventCreate(EventBase):
    pass


# Properties to receive via API on update, all are optional
class EventUpdate(EventBase):
    pass


# Database model, database table inferred from class name
class Event(mixin.RowId, EventBase, table=True):
    # --- database only items --------------------------------------------------

    # --- back_populates links -------------------------------------------------

    # --- many-to-many links ---------------------------------------------------
    user_links: list["EventUserLink"] = Relationship(back_populates="event", cascade_delete=True)
    team_links: list["Team"] = Relationship(back_populates="event", cascade_delete=True)

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: EventCreate) -> "Event":
        data_obj = create_obj.model_dump(exclude_unset=True)

        db_obj = cls.model_validate(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(
        cls, *, session: Session, db_obj: "Event", in_obj: EventUpdate
    ) -> "Event":
        data_obj = in_obj.model_dump(exclude_unset=True)

        db_obj.sqlmodel_update(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def get_user_link(self, user: User) -> EventUserLink | None:
        return next(
            (link for link in self.user_links if link.user == user), None
        )

    def add_user(
        self,
        user: User,
        rights: PermissionRight = PermissionRight.READ,
        *,
        session: Session,
    ) -> "EventUserLink | None":
        to_add = self.get_user_link(user=user)

        if to_add is None:
            self.user_links.append(EventUserLink(event=self, user=user, rights=rights))
            session.add(self.user_links[-1])
            session.commit()
            return self.user_links[-1]

        return None

    def update_user(
        self,
        user: User,
        rights: PermissionRight = PermissionRight.READ,
        *,
        session: Session,
    ) -> "EventUserLink | None":
        to_update = self.get_user_link(user=user)

        if to_update:
            to_update.rights = rights
            session.add(to_update)
            session.commit()
            return to_update

        return None

    def remove_user(self, user: User, *, session: Session) -> None:
        to_remove = self.get_user_link(user=user)
        if to_remove:
            session.delete(to_remove)
            session.commit()


    def user_has_rights(
        self,
        user: User,
        rights: PermissionRight | None = None,
    ) -> bool:
        """
        Check if all rights are present for the user
        """
        return any(
            (
                link.user == user
                and link.rights
                and (not rights or (link.rights & rights) == rights)
            )
            for link in self.user_links
        )

    def user_has_right(
        self,
        user: User,
        rights: PermissionRight | None = None,
    ) -> bool:
        """
        Check if at least one right is present for the user
        """
        return any(
            (
                link.user == user
                and link.rights
                and (not rights or (link.rights & rights))
            )
            for link in self.user_links
        )


# Properties to return via API, id is always required
class EventPublic(mixin.RowIdPublic, EventBase):
    pass


class EventsPublic(BaseSQLModel):
    data: list[EventPublic]
    count: int


# endregion
