from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.base import (
    ApiTags,
    Message,
    RowId,
)
from app.models.event import (
    Event,
    EventCreate,
    EventPublic,
    EventsPublic,
    EventUpdate,
    EventUserLink,
    EventTeam,
    EventTeamCreate,
    EventTeamPublic,
    EventTeamsPublic,
)
from app.models.user import (
    PermissionModule,
    PermissionPart,
    PermissionRight,
    PermissionRightObject,
    User,
)

router = APIRouter(prefix="/events", tags=[ApiTags.EVENTS])

# region # Events ##############################################################


@router.get("/", response_model=EventsPublic)
def read_events(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve events.
    """

    if current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ):
        count_statement = select(func.count()).select_from(Event)
        count = session.exec(count_statement).one()
        statement = select(Event).offset(skip).limit(limit)
        events = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Event)
            .where(
                EventUserLink.user_id == current_user.id,
                (EventUserLink.rights & PermissionRight.READ) == PermissionRight.READ,
            )
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Event)
            .where(
                EventUserLink.user_id == current_user.id,
                (EventUserLink.rights & PermissionRight.READ) == PermissionRight.READ,
            )
            .offset(skip)
            .limit(limit)
        )
        events = session.exec(statement).all()

    return EventsPublic(data=events, count=count)


@router.get("/{id}", response_model=EventPublic)
def read_event(session: SessionDep, current_user: CurrentUser, id: RowId) -> Any:
    """
    Get event by ID.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ) and (event.user_has_rights(user=current_user, rights=PermissionRight.READ)):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return event


@router.post("/", response_model=EventPublic)
def create_event(
    *, session: SessionDep, current_user: CurrentUser, event_in: EventCreate
) -> Any:
    """
    Create new event.
    """
    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.CREATE,
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    event = Event.create(create_obj=event_in, session=session)
    event.add_user(user=current_user, rights=PermissionRight.ADMIN, session=session)
    return event


@router.put("/{id}", response_model=EventPublic)
def update_event(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: RowId,
    event_in: EventUpdate,
) -> Any:
    """
    Update an event.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.UPDATE,
    ) and (event.user_has_rights(user=current_user, rights=PermissionRight.UPDATE)):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return Event.update(db_obj=event, in_obj=event_in, session=session)


@router.delete("/{id}")
def delete_event(
    session: SessionDep,
    current_user: CurrentUser,
    id: RowId,
) -> Message:
    """
    Delete an event.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.DELETE,
    ) and (event.user_has_rights(user=current_user, rights=PermissionRight.DELETE)):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    session.delete(event)
    session.commit()
    return Message(message="Event deleted successfully")


# endregion


# region # Events / Users ######################################################


@router.post("/{id}/users/{user_id}", tags=[ApiTags.USERS])
def add_user_to_event(
    session: SessionDep,
    current_user: CurrentUser,
    id: RowId,
    user_id: RowId,
    rights_in: PermissionRightObject,
) -> Message:
    """
    Add or update a user to an event.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_USERS,
    ) and (
        event.user_has_rights(
            user=current_user, rights=(PermissionRight.MANAGE_USERS | rights_in.rights)
        )
    ):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    user = session.get(User, user_id)
    if not event:
        raise HTTPException(status_code=404, detail="User not found")

    event.add_user(user=user, rights=rights_in.rights, session=session)
    return Message(
        message="User added successfully"
    )  # TODO: Return event or event_users


@router.delete("/{id}/users/{user_id}", tags=[ApiTags.USERS])
def remove_user_from_event(
    session: SessionDep, current_user: CurrentUser, id: RowId, user_id: RowId
) -> Message:
    """
    Remove a user from an event.
    """
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_USERS,
    ) and not event.user_has_rights(
        user=current_user, rights=PermissionRight.MANAGE_USERS
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event.remove_user(user=user, session=session)
    return Message(
        message="User removed successfully"
    )  # TODO: Return event or event_users


# endregion


# region # Event / Teams #######################################################

@router.get("/{id}/teams", response_model=EventTeamsPublic, tags=router.tags + [ApiTags.TEAMS])
def read_event_teams(
    session: SessionDep, current_user: CurrentUser, id: RowId, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve event teams from a single event.
    """

    # Event permissions
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=(PermissionRight.READ | PermissionRight.MANGE_TEAMS),
    ) and ( event and (event.user_has_rights(user=current_user, rights=(PermissionRight.READ | PermissionRight.MANGE_TEAMS)))):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Get list
    count_statement = (
        select(func.count())
        .select_from(EventTeam)
        .where(EventTeam.event_id == id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(EventTeam)
        .where(EventTeam.event_id == id)
        .offset(skip)
        .limit(limit)
    )
    event_teams = session.exec(statement).all()

    return EventTeamsPublic(data=event_teams, count=count)


@router.post("/{id}/teams", response_model=EventTeamPublic, tags=router.tags + [ApiTags.TEAMS])
def create_event_team(
    *, session: SessionDep, current_user: CurrentUser, id: RowId, event_team_in: EventTeamCreate
) -> Any:
    """
    Create new team inside event.
    """

    event = session.get(Event, id)

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANGE_TEAMS,
    ) and ( event and (event.user_has_rights(user=current_user, rights=PermissionRight.MANGE_TEAMS))):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    event_team = EventTeam.create(create_obj=event_team_in, event=event, session=session)
    return event_team


@router.get("/teams", response_model=EventTeamsPublic, tags=router.tags + [ApiTags.TEAMS])
def read_event_teams(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all event teams.
    """

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANGE_TEAMS,
    ):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Get list
    count_statement = (
        select(func.count())
        .select_from(EventTeam)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(EventTeam)
        .offset(skip)
        .limit(limit)
    )
    event_teams = session.exec(statement).all()

    return EventTeamsPublic(data=event_teams, count=count)


@router.get("/teams/{id}", response_model=EventTeamPublic, tags=router.tags + [ApiTags.TEAMS])
def read_event_team(session: SessionDep, current_user: CurrentUser, id: RowId) -> Any:
    """
    Get event team by ID.
    """
    event_team = session.get(EventTeam, id)
    if not event_team:
        raise HTTPException(status_code=404, detail="Event team not found")

    event = session.get(Event, event_team.event_id)

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANGE_TEAMS,
    ) and ( event and (event.user_has_rights(user=current_user, rights=PermissionRight.MANGE_TEAMS))):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    return event_team


@router.put("/teams/{id}", response_model=EventTeamPublic, tags=router.tags + [ApiTags.TEAMS])
def create_event_team(
    *, session: SessionDep, current_user: CurrentUser, id: RowId, event_team_in: EventTeamCreate
) -> Any:
    """
    Update team.
    """
    event_team = session.get(EventTeam, id)
    if not event_team:
        raise HTTPException(status_code=404, detail="Event team not found")

    event = session.get(Event, event_team.event_id)

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANGE_TEAMS,
    ) and ( event and (event.user_has_rights(user=current_user, rights=PermissionRight.MANGE_TEAMS))):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    event_team = EventTeam.update(db_obj=event_team, in_obj=event_team_in, session=session)
    return event_team


@router.delete("/teams/{id}", tags=router.tags + [ApiTags.TEAMS])
def delete_event_team(session: SessionDep,current_user: CurrentUser, id: RowId) -> Message:
    """
    Delete an event team.
    """
    event_team = session.get(EventTeam, id)
    if not event_team:
        raise HTTPException(status_code=404, detail="Event team not found")

    event = session.get(Event, event_team.event_id)

    if not current_user.has_permission(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANGE_TEAMS,
    ) and (event.user_has_rights(user=current_user, rights=PermissionRight.MANGE_TEAMS)):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    session.delete(event_team)
    session.commit()
    return Message(message="Event team deleted successfully")

# endregion