from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.base import (
    ApiTags,
    Message,
    RowId,
)
from app.models.division import (
    Division,
    DivisionCreate,
    DivisionUpdate,
    DivisionPublic,
    DivisionsPublic,
)
from app.models.user import (
    PermissionModule,
    PermissionPart,
    PermissionRight,
)

router = APIRouter(prefix="/divisions", tags=[ApiTags.DIVISIONS])


# region # Divisions ###########################################################

@router.get("/", response_model=DivisionsPublic)
def read_divisions(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all divisions.
    """

    if current_user.has_permissions(
        module=PermissionModule.DIVISION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ):
        count_statement = select(func.count()).select_from(Division)
        count = session.exec(count_statement).one()
        statement = select(Division).offset(skip).limit(limit)
        divisions = session.exec(statement).all()
        return DivisionsPublic(data=divisions, count=count)

    return DivisionsPublic(data=[], count=0)


@router.get("/{id}", response_model=DivisionPublic)
def read_division(session: SessionDep, current_user: CurrentUser, id: RowId) -> Any:
    """
    Get division by ID.
    """
    division = session.get(Division, id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")

    if not current_user.has_permissions(
        module=PermissionModule.DIVISION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return division


@router.post("/", response_model=DivisionPublic)
def create_division(
    *, session: SessionDep, current_user: CurrentUser, division_in: DivisionCreate
) -> Any:
    """
    Create new division.
    """

    if not current_user.has_permissions(
        module=PermissionModule.DIVISION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.CREATE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    division = Division.create(create_obj=division_in, session=session)
    return division


@router.put("/{id}", response_model=DivisionPublic)
def update_division(
    *, session: SessionDep, current_user: CurrentUser, id: RowId, division_in: DivisionUpdate
) -> Any:
    """
    Update a division.
    """
    division = session.get(Division, id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")

    if not current_user.has_permissions(
        module=PermissionModule.DIVISION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.UPDATE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    division = Division.update(db_obj=division, in_obj=division_in, session=session)
    return division


@router.delete("/{id}")
def delete_division(session: SessionDep,current_user: CurrentUser, id: RowId) -> Message:
    """
    Delete a division.
    """
    division = session.get(Division, id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")

    if not current_user.has_permissions(
        module=PermissionModule.ASSOCIATION,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.DELETE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    session.delete(division)
    session.commit()
    return Message(message="Division deleted successfully")

# endregion
