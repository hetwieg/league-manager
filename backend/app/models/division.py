from typing import TYPE_CHECKING

from sqlalchemy.orm.sync import update
from sqlmodel import (
    Session,
    Field,
    Relationship,
)

from . import mixin
from .base import (
    BaseSQLModel,
    RowId,
)

if TYPE_CHECKING:
    from .association import Association
    from .team import Team


# region # Divisions / Team Link ######################################

class DivisionTeamLinkBase(
    mixin.Name,
    BaseSQLModel,
):
    pass


class DivisionTeamLinkCreate(DivisionTeamLinkBase):
    division_id: RowId | None = Field(default=None)


class DivisionTeamLinkUpdate(DivisionTeamLinkBase):
    pass


class DivisionTeamLink(DivisionTeamLinkBase, table=True):
    # --- database only items --------------------------------------------------

    # --- read only items ------------------------------------------------------
    team_id: RowId = Field(
        default=None,
        foreign_key="team.id",
        nullable=False,
        ondelete="CASCADE",
        primary_key=True,
    )

    # --- back_populates links -------------------------------------------------
    division_id: RowId = Field(
        default=None,
        foreign_key="division.id",
        nullable=False,
        ondelete="CASCADE",
    )
    division: "Division" = Relationship(back_populates="team_links")
    team: "Team" = Relationship(back_populates="division_link")

    # Members (1 lid > meerdere teams | many-to-one)

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: DivisionTeamLinkCreate, team: "Team") -> "DivisionTeamLink":
        data_obj = create_obj.model_dump(exclude_unset=True)

        db_obj = cls.model_validate(data_obj, update={"team_id": team.id})
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(
        cls, *, session: Session, db_obj: "DivisionTeamLink", in_obj: DivisionTeamLinkUpdate
    ) -> "DivisionTeamLink":
        data_obj = in_obj.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj


# Properties to return via API, id is always required
class DivisionTeamLinkPublic(DivisionTeamLinkBase):
    team_id: RowId
    division_id: RowId



# endregion


# region # Divisions ###########################################################


class DivisionBase(
    mixin.Name,
    mixin.Contact,
    mixin.ScoutingId,
    BaseSQLModel,
):
    association_id: RowId = Field(
        foreign_key="association.id", nullable=False, ondelete="CASCADE"
    )


# Properties to receive via API on creation
class DivisionCreate(DivisionBase):
    pass


# Properties to receive via API on update, all are optional
class DivisionUpdate(DivisionBase):
    association_id: RowId | None = Field(default=None)


class Division(mixin.RowId, DivisionBase, table=True):
    # --- database only items --------------------------------------------------

    # --- read only items ------------------------------------------------------

    # --- back_populates links -------------------------------------------------
    association: "Association" = Relationship(back_populates="divisions")
    team_links: list["DivisionTeamLink"] = Relationship(back_populates="division", cascade_delete=True)

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: DivisionCreate) -> "Division":
        data_obj = create_obj.model_dump(exclude_unset=True)

        db_obj = cls.model_validate(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(
        cls, *, session: Session, db_obj: "Division", in_obj: DivisionUpdate
    ) -> "Division":
        data_obj = in_obj.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj


# Properties to return via API, id is always required
class DivisionPublic(mixin.RowIdPublic, DivisionBase):
    association_id: RowId


class DivisionsPublic(BaseSQLModel):
    data: list[DivisionPublic]
    count: int


# endregion
