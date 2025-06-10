from typing import TYPE_CHECKING

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
    association: "Association" = Relationship(back_populates="divisions")  # , cascade_delete=True)

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
