from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.base import (
    ApiTags,
    Message,
    RowId,
)
from app.models.team import (
    Team,
    TeamCreate,
    TeamUpdate,
    TeamPublic,
    TeamsPublic,
)
from app.models.event import (
    Event,
    EventUserLink,
)
from app.models.user import (
    PermissionModule,
    PermissionPart,
    PermissionRight,
)
from app.models.division import (
    DivisionTeamLink,
    DivisionTeamLinkCreate,
    DivisionTeamLinkUpdate,
    DivisionTeamLinkPublic,
)

router = APIRouter(prefix="/teams", tags=[ApiTags.TEAMS])


# region # Teams ###############################################################

@router.get("/", response_model=TeamsPublic)
def read_teams(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all teams.
    """

    if current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ):
        count_statement = select(func.count()).select_from(Team)
        count = session.exec(count_statement).one()
        statement = select(Team).offset(skip).limit(limit)
        teams = session.exec(statement).all()

    else:
        # Only read teams that are connected to an event that the user can read
        count_statement = (
            select(func.count())
            .select_from(Team)
            .join(Event)  # Join with Event to filter teams based on events
            .join(EventUserLink)  # Join with EventUserLink to check user permissions
            .where(
                EventUserLink.user_id == current_user.id,
                # FIXME: (EventUserLink.rights & (PermissionRight.READ | PermissionRight.MANAGE_TEAMS)) > 0
            )
        )
        count = session.exec(count_statement).one()

        statement = (
            select(Team)
            .join(Event)
            .join(EventUserLink)
            .where(
                EventUserLink.user_id == current_user.id,
                # FIXME: (EventUserLink.rights & (PermissionRight.READ | PermissionRight.MANAGE_TEAMS)) > 0
            )
            .offset(skip)
            .limit(limit)
        )
        teams = session.exec(statement).all()

    return TeamsPublic(data=teams, count=count)


@router.get("/{id}", response_model=TeamPublic)
def read_team(session: SessionDep, current_user: CurrentUser, id: RowId) -> Any:
    """
    Get team by ID.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
            module=PermissionModule.TEAM,
            part=PermissionPart.ADMIN,
            rights=PermissionRight.READ,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_TEAMS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return team


@router.post("/", response_model=TeamPublic)
def create_team(
    *, session: SessionDep, current_user: CurrentUser, team_in: TeamCreate
) -> Any:
    """
    Create new team.
    """

    event = session.get(Event, team_in.event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.UPDATE,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_TEAMS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    team = Team.create(create_obj=team_in, session=session)
    return team


@router.put("/{id}", response_model=TeamPublic)
def update_team(
    *, session: SessionDep, current_user: CurrentUser, id: RowId, team_in: TeamUpdate
) -> Any:
    """
    Update a team.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check user's permissions for the existing event
    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.UPDATE,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_TEAMS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Check rights for the new event data
    if team_in.event_id:
        event = session.get(Event, team_in.event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New event not found")

        if not current_user.has_permissions(
                module=PermissionModule.TEAM,
                part=PermissionPart.ADMIN,
                rights=PermissionRight.UPDATE,
        ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_TEAMS)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Update the team
    team = Team.update(db_obj=team, in_obj=team_in, session=session)
    return team


@router.delete("/{id}")
def delete_team(session: SessionDep,current_user: CurrentUser, id: RowId) -> Message:
    """
    Delete a team.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.DELETE,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_TEAMS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    session.delete(team)
    session.commit()
    return Message(message="Team deleted successfully")

# endregion


# region # Teams / Division ####################################################

@router.get("/{id}/division", response_model=DivisionTeamLinkPublic, tags=[ApiTags.DIVISIONS])
def read_team_divisions(session: SessionDep, current_user: CurrentUser, id: RowId) -> Any:
    """
    Get division from team by ID.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
            module=PermissionModule.TEAM,
            part=PermissionPart.ADMIN,
            rights=PermissionRight.MANAGE_DIVISIONS,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_DIVISIONS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return team.division_link


@router.post("/{id}/division", response_model=DivisionTeamLinkPublic, tags=[ApiTags.DIVISIONS])
def create_team_division_link(
    *, session: SessionDep, current_user: CurrentUser, team_in: DivisionTeamLinkCreate, id: RowId
) -> Any:
    """
    Create new division link in team.
    """

    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if team.division_link:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team already linked to division")

    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_DIVISIONS,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_DIVISIONS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    division_team_link = DivisionTeamLink.create(create_obj=team_in, session=session, team=team)
    return division_team_link


@router.put("/{id}/division", response_model=DivisionTeamLinkPublic, tags=[ApiTags.DIVISIONS])
def update_team_division_link(
    *, session: SessionDep, current_user: CurrentUser, id: RowId, team_in: DivisionTeamLinkUpdate
) -> Any:
    """
    Update division info inside team.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check user's permissions for the existing event
    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_DIVISIONS,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_DIVISIONS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Update the team
    division_team_link = DivisionTeamLink.update(db_obj=team.division_link, in_obj=team_in, session=session)
    return division_team_link


@router.delete("/{id}/division", tags=[ApiTags.DIVISIONS])
def delete_team_division_link(session: SessionDep, current_user: CurrentUser, id: RowId) -> Message:
    """
    Delete a division link from a team.
    """
    team = session.get(Team, id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    event = session.get(Event, team.event_id)
    if not event: # pragma: no cover
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.TEAM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_DIVISIONS,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_DIVISIONS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    session.delete(team.division_link)
    session.commit()
    return Message(message="Division deleted from team successfully")

# endregion
