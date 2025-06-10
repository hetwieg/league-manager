from typing import TYPE_CHECKING

from sqlmodel import (
    Session,
)

from . import mixin
from .base import (
    BaseSQLModel,
)

# region # Association #########################################################


class AssociationBase(
    mixin.Name,
    mixin.Contact,
    mixin.ScoutingId,
    BaseSQLModel,
):
    pass


# Properties to receive via API on creation
class AssociationCreate(AssociationBase):
    pass


# Properties to receive via API on update, all are optional
class AssociationUpdate(AssociationBase):
    pass


class Association(mixin.RowId, AssociationBase, table=True):
    # --- database only items --------------------------------------------------

    # --- read only items ------------------------------------------------------

    # --- back_populates links -------------------------------------------------

    # --- CRUD actions ---------------------------------------------------------
    @classmethod
    def create(cls, *, session: Session, create_obj: AssociationCreate) -> "Association":
        data_obj = create_obj.model_dump(exclude_unset=True)

        db_obj = cls.model_validate(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    @classmethod
    def update(
        cls, *, session: Session, db_obj: "Association", in_obj: AssociationUpdate
    ) -> "Association":
        data_obj = in_obj.model_dump(exclude_unset=True)
        db_obj.sqlmodel_update(data_obj)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj


# Properties to return via API, id is always required
class AssociationPublic(mixin.RowIdPublic, AssociationBase):
    pass


class AssociationsPublic(BaseSQLModel):
    data: list[AssociationPublic]
    count: int


# endregion
