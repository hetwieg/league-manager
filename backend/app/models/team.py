from typing import TYPE_CHECKING

from sqlmodel import (
    Field,
    Relationship,
    Session,
)

from . import mixin
from .base import (
    BaseSQLModel,
    RowId,
)

if TYPE_CHECKING:
    from .event import Event

# region # Team ################################################################


class TeamBase(
    mixin.ThemeName,
    mixin.CheckInCheckOut,
    mixin.Canceled,
    BaseSQLModel
):
    event_id: RowId = Field(
        foreign_key="event.id", nullable=False, ondelete="CASCADE"
    )
    # scouting_team_id: RowId | None = Field(
    #     foreign_key="ScoutingTeam.id", nullable=False, ondelete="CASCADE"
    # )


# Properties to receive via API on creation
class TeamCreate(TeamBase):
    pass


# Properties to receive via API on update, all are optional
class TeamUpdate(mixin.ThemeNameUpdate, TeamBase):
    event_id: RowId | None = Field(default=None)


class Team(mixin.RowId, TeamBase, table=True):
    # --- database only items --------------------------------------------------

    # --- read only items ------------------------------------------------------

    # --- back_populates links -------------------------------------------------
    event: "Event" = Relationship(back_populates="team_links")#, cascade_delete=True)
    # team: "ScoutingTeam" = Relationship(back_populates="event_links", cascade_delete=True)

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: TeamCreate) -> "Team":
        data_obj = create_obj.model_dump(exclude_unset=True)

        db_obj = cls.model_validate(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(
        cls, *, session: Session, db_obj: "Team", in_obj: TeamUpdate
    ) -> "Team":
        data_obj = in_obj.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj


# Properties to return via API, id is always required
class TeamPublic(mixin.RowIdPublic, TeamBase):
    event_id: RowId


class TeamsPublic(BaseSQLModel):
    data: list[TeamPublic]
    count: int


# endregion