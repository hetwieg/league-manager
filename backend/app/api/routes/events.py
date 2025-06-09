from typing import Any

from fastapi import APIRouter, HTTPException, status
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
    EventUserLinkCreate,
    EventUserLinkUpdate,
    EventUserLinkPublic,
    EventUserLinksPublic,
)
from app.models.user import (
    PermissionModule,
    PermissionPart,
    PermissionRight,
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

    if current_user.has_permissions(
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
            .join(EventUserLink)  # Join with EventUserLink to check user permissions
            .where(
                EventUserLink.user_id == current_user.id,
                # FIXME: (EventUserLink.rights & PermissionRight.READ) == PermissionRight.READ,
            )
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Event)
            .join(EventUserLink)  # Join with EventUserLink to check user permissions
            .where(
                EventUserLink.user_id == current_user.id,
                # FIXME: (EventUserLink.rights & PermissionRight.READ) == PermissionRight.READ,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.READ,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.READ)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return event


@router.post("/", response_model=EventPublic)
def create_event(
    *, session: SessionDep, current_user: CurrentUser, event_in: EventCreate
) -> Any:
    """
    Create new event.
    """
    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.CREATE,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.UPDATE,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.UPDATE)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.DELETE,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.DELETE)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    session.delete(event)
    session.commit()
    return Message(message="Event deleted successfully")


# endregion


# region # Events / Users ######################################################


@router.get("/{event_id}/users/", response_model=EventUserLinksPublic)
def read_event_users(
    session: SessionDep, current_user: CurrentUser, event_id: RowId, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve all event users.
    """

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_USERS,
    ) and not (event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_USERS)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    count_statement = (select(func.count())
                       .select_from(EventUserLink)
                       .where(EventUserLink.event_id == event.id)
                       )
    count = session.exec(count_statement).one()
    statement = (select(EventUserLink)
                 .where(EventUserLink.event_id == event.id)
                 .offset(skip)
                 .limit(limit)
                 )
    event_user_links = session.exec(statement).all()

    return EventUserLinksPublic(data=event_user_links, count=count)


@router.post("/{event_id}/users/", tags=[ApiTags.USERS], response_model=EventUserLinkPublic)
def create_event_user(
    session: SessionDep,
    current_user: CurrentUser,
    event_id: RowId,
    user_in: EventUserLinkCreate,
) -> Any:
    """
    Create a new link between a user and an event.
    """

    if user_in.rights & ~PermissionRight.ADMIN:
        # FIXME: find a proper richts checker
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid permission rights")

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_USERS,
    ) and not (event.user_has_rights(user=current_user, rights=(PermissionRight.MANAGE_USERS | user_in.rights))):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    user = session.get(User, user_in.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_link = event.get_user_link(user)
    if user_link:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already part of this event")

    return event.add_user(user=user, rights=user_in.rights, session=session)


@router.put("/{event_id}/users/{user_id}", tags=[ApiTags.USERS], response_model=EventUserLinkPublic)
def update_user_in_event(
    session: SessionDep,
    current_user: CurrentUser,
    event_id: RowId,
    user_id: RowId,
    user_in: EventUserLinkUpdate,
) -> Any:
    """
    Update a user link within an event.
    """

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    valid_flags = sum(flag.value for flag in PermissionRight)
    if user_in.rights & ~valid_flags:
        # FIXME: find a proper richts checker
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid permission rights")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_USERS,
    ) and not (event.user_has_rights(user=current_user, rights=(PermissionRight.MANAGE_USERS | user_in.rights))):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    user_link = event.get_user_link(user)
    if not user_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not part of this event")

    return event.update_user(user=user, rights=user_in.rights, session=session)


@router.delete("/{event_id}/users/{user_id}", tags=[ApiTags.USERS])
def remove_user_from_event(
    session: SessionDep, current_user: CurrentUser, event_id: RowId, user_id: RowId
) -> Message:
    """
    Remove a user link from an event.
    """
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not current_user.has_permissions(
        module=PermissionModule.EVENT,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.MANAGE_USERS,
    ):
        if current_user.id == user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Users are not allowed to delete themselves when they are not an super admin")

        if not event.user_has_rights(user=current_user, rights=PermissionRight.MANAGE_USERS):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    user_link = event.get_user_link(user)
    if not user_link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not part of this event")

    event.remove_user(user=user, session=session)
    return Message(
        message="User removed successfully"
    )


# endregion
