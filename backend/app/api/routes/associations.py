from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.base import (
    ApiTags,
    Message,
    RowId,
)
from app.models.association import (
    Association,
    AssociationCreate,
    AssociationUpdate,
    AssociationPublic,
    AssociationsPublic,
)
from app.models.division import (
    Division,
    DivisionsPublic,
)
from app.models.user import (
    PermissionModule,
    PermissionPart,
    PermissionRight,
)

router = APIRouter(prefix="/associations", tags=[ApiTags.ASSOCIATIONS])


# region # Associations ########################################################

@router.get("/", response_model=AssociationsPublic)
def read_associations(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all associations.
    """

    if current_user.has_permissions(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ):
        count_statement = select(func.count()).select_from(Association)
        count = session.exec(count_statement).one()
        statement = select(Association).offset(skip).limit(limit)
        associations = session.exec(statement).all()
        return AssociationsPublic(data=associations, count=count)

    return AssociationsPublic(data=[], count=0)


@router.get("/{id}", response_model=AssociationPublic)
def read_association(session: SessionDep, current_user: CurrentUser, id: RowId) -> Any:
    """
    Get association by ID.
    """
    association = session.get(Association, id)
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")

    if not current_user.has_permissions(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return association


@router.post("/", response_model=AssociationPublic)
def create_association(
    *, session: SessionDep, current_user: CurrentUser, association_in: AssociationCreate
) -> Any:
    """
    Create new association.
    """

    if not current_user.has_permissions(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.CREATE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    association = Association.create(create_obj=association_in, session=session)
    return association


@router.put("/{id}", response_model=AssociationPublic)
def update_association(
    *, session: SessionDep, current_user: CurrentUser, id: RowId, association_in: AssociationUpdate
) -> Any:
    """
    Update a association.
    """
    association = session.get(Association, id)
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")

    if not current_user.has_permissions(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.UPDATE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    association = Association.update(db_obj=association, in_obj=association_in, session=session)
    return association


@router.delete("/{id}")
def delete_association(session: SessionDep,current_user: CurrentUser, id: RowId) -> Message:
    """
    Delete a association.
    """
    association = session.get(Association, id)
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")

    if not current_user.has_permissions(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.DELETE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    session.delete(association)
    session.commit()
    return Message(message="Association deleted successfully")

# endregion


# region # Associations / Divisions ############################################


@router.get("/{associations_id}/divisions/", response_model=DivisionsPublic)
def read_association_division(
    session: SessionDep, current_user: CurrentUser, associations_id: RowId, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all association divisions.
    """

    association = session.get(Association, associations_id)
    if not association:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Association not found")

    if not current_user.has_permission(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=(PermissionRight.MANAGE_DIVISIONS | PermissionRight.READ),
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    count_statement = (select(func.count())
                       .select_from(Division)
                       .where(Division.association_id == association.id)
                       )
    count = session.exec(count_statement).one()
    statement = (select(Division)
                 .where(Division.association_id == association.id)
                 .offset(skip)
                 .limit(limit)
                 )
    divisions = session.exec(statement).all()

    return DivisionsPublic(data=divisions, count=count)


# endregion
