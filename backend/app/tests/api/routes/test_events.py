import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.user import PermissionRight
from app.tests.conftest import EventUserHeader
from app.tests.utils.event import create_random_event
from app.tests.utils.user import create_random_user, authentication_token_from_user


def test_create_event(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "name": "Foo",
        "contact": "Someone",
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert "id" in content
    assert "is_active" in content
    assert "start_at" in content
    assert "end_at" in content


def test_create_event_no_permission(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    data = {
        "name": "No create permission",
        "contact": "Someone else",
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"



def test_read_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == event.name
    assert content["contact"] == event.contact
    assert content["id"] == str(event.id)
    assert content["is_active"] == event.is_active
    assert str(content["start_at"]) == str(event.start_at)
    assert str(content["end_at"]) == str(event.end_at)


def test_read_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


def test_read_event_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_event_with_event_user(
    client: TestClient, event_user_token_headers: EventUserHeader, db: Session
) -> None:
    event = event_user_token_headers.event
    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=event_user_token_headers.headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == event.name
    assert content["contact"] == event.contact
    assert content["id"] == str(event.id)
    assert content["is_active"] == event.is_active
    assert str(content["start_at"]) == str(event.start_at)
    assert str(content["end_at"]) == str(event.end_at)


def test_read_events(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_event(db)
    create_random_event(db)
    response = client.get(
        f"{settings.API_V1_STR}/events/",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] >= 2
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) <= content["count"]


def test_read_events_with_event_user(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    response = client.get(
        f"{settings.API_V1_STR}/events/",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] == 1
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) <= content["count"]


def test_update_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    data = {
        "name": "Updated name",
        "contact": "Updated contact",
    }
    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert content["id"] == str(event.id)
    assert content["is_active"] == event.is_active
    assert str(content["start_at"]) == str(event.start_at)
    assert str(content["end_at"]) == str(event.end_at)


def test_update_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Updated name", "contact": "Updated contact"}
    response = client.put(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


def test_update_event_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    data = {"name": "Updated name", "contact": "Updated contact"}
    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_update_event_with_eventuser(
    client: TestClient, event_user_token_headers: EventUserHeader, db: Session
) -> None:
    event = event_user_token_headers.event
    data = {
        "name": "Updated name from eventuser",
        "contact": "Updated contact from eventuser",
    }
    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=event_user_token_headers.headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert content["id"] == str(event.id)
    assert content["is_active"] == event.is_active
    assert str(content["start_at"]) == str(event.start_at)
    assert str(content["end_at"]) == str(event.end_at)


def test_delete_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Event deleted successfully"


def test_delete_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = response.json()
    assert content["detail"] == "Event not found"


def test_delete_event_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_event_admin_user(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.ADMIN, session=db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["message"] == "Event deleted successfully"


def test_delete_event_not_enough_permissions_for_this_event(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_event_event_user_read_only_rights(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_all_event_users(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user1 = create_random_user(db)
    user2 = create_random_user(db)
    event.add_user(user=user1, rights=PermissionRight.READ, session=db)
    event.add_user(user=user2, rights=PermissionRight.ADMIN, session=db)

    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] == 2
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) <= content["count"]


def test_read_all_event_users_no_permission(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)

    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_all_event_users_with_event_user(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.MANAGE_USERS, session=db)

    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] == 1
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) <= content["count"]


def test_read_all_event_users_with_event_user_no_permission(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_add_user_to_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}/users",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


def test_add_user_to_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    data = {
        "user_id": str(user.id),
        "rights": PermissionRight.READ,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "rights" in content
    assert content["rights"] == PermissionRight.READ
    assert content["user_id"] == str(user.id)
    assert content["event_id"] == str(event.id)


def test_add_user_to_event_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user = create_random_user(db)
    data = {
        "user_id": str(user.id),
        "rights": PermissionRight.READ,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}/users",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


def test_add_user_to_event_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    data = {
        "user_id": str(uuid.uuid4()),
        "rights": PermissionRight.READ,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_add_user_to_event_already_exists(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)
    data = {
        "user_id": str(user.id),
        "rights": PermissionRight.ADMIN,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "User already part of this event"


def test_add_user_to_event_no_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    data = {
        "user_id": str(user.id),
        "rights": PermissionRight.READ,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_add_user_to_event_unknown_rights(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    data = {
        "user_id": str(user.id),
        "rights": -1,  # Invalid permission value
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid permission rights"


def test_add_user_with_more_rights_than_current_user(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    limited_user = create_random_user(db)
    event.add_user(user=limited_user, rights=PermissionRight.MANAGE_USERS, session=db)

    target_user = create_random_user(db)

    data = {
        "user_id": str(target_user.id),
        "rights": PermissionRight.ADMIN,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=authentication_token_from_user(db=db, user=limited_user, client=client),
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.xfail(reason="Combined rights add might not yet be supported")
def test_add_user_rights_combined(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)

    data = {
        "rights": PermissionRight.READ | PermissionRight.UPDATE,
    }

    response = client.post(
        f"{settings.API_V1_STR}/events/{event.id}/users",
        headers=superuser_token_headers,
        json=data,
    )

    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "rights" in content
    assert content["rights"] == data["rights"]
    assert content["event_id"] == str(event.id)


def test_update_user_inside_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)
    data = {
        "rights": PermissionRight.UPDATE,
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "rights" in content
    assert content["rights"] == data["rights"]
    assert content["user_id"] == str(user.id)
    assert content["event_id"] == str(event.id)


def test_update_event_user_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
):
    user = create_random_user(db)
    data = {
        "rights": PermissionRight.UPDATE,
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


def test_update_event_user_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
):
    event = create_random_event(db)
    data = {
        "rights": PermissionRight.UPDATE,
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_update_event_user_unknown_rights(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
):
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)
    data = {
        "rights": -1,  # Invalid permission value
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid permission rights"


def test_update_event_user_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
):
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.ADMIN, session=db)
    data = {
        "rights": PermissionRight.READ
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_update_event_user_with_event_user_same_event(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user1 = create_random_user(db)
    user2 = create_random_user(db)

    event.add_user(user=user1, rights=PermissionRight.ADMIN, session=db)
    event.add_user(user=user2, rights=PermissionRight.READ, session=db)

    data = {
        "rights": PermissionRight.UPDATE,
    }

    # event_user1 tries to update event_user2 rights
    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user2.id}",
        headers=authentication_token_from_user(db=db, user=user1, client=client),
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["rights"] == data["rights"]
    assert content["user_id"] == str(user2.id)
    assert content["event_id"] == str(event.id)


def test_update_event_user_from_other_event_forbidden(
    client: TestClient, db: Session
) -> None:
    event1 = create_random_event(db)
    event2 = create_random_event(db)

    user1 = create_random_user(db)
    user2 = create_random_user(db)

    event1.add_user(user=user1, rights=PermissionRight.ADMIN, session=db)
    event2.add_user(user=user2, rights=PermissionRight.READ, session=db)

    data = {
        "rights": PermissionRight.UPDATE,
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event2.id}/users/{user2.id}",
        headers=authentication_token_from_user(db=db, user=user1, client=client),
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_update_event_user_from_other_event_thru_own_event(
    client: TestClient, db: Session
) -> None:
    event1 = create_random_event(db)
    event2 = create_random_event(db)

    user1 = create_random_user(db)
    user2 = create_random_user(db)

    event1.add_user(user=user1, rights=PermissionRight.ADMIN, session=db)
    event2.add_user(user=user2, rights=PermissionRight.READ, session=db)

    data = {
        "rights": PermissionRight.UPDATE,
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event1.id}/users/{user2.id}",
        headers=authentication_token_from_user(db=db, user=user1, client=client),
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User is not part of this event"


@pytest.mark.xfail(reason="Combined rights update might not yet be supported")
def test_update_user_rights_combined(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    # Initially assign READ only rights
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    data = {
        "rights": PermissionRight.READ | PermissionRight.UPDATE,
    }

    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "rights" in content
    assert content["rights"] == data["rights"]
    assert content["user_id"] == str(user.id)
    assert content["event_id"] == str(event.id)


def test_remove_user_from_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "User removed successfully"
    # assert not event.get_user_link(user)


def test_remove_user_from_event_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Event not found"


def test_remove_user_from_event_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found"


def test_remove_user_from_event_user_not_in_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User is not part of this event"


def test_remove_user_from_event_insufficient_permissions(
    client: TestClient, db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.READ, session=db)

    limited_user = create_random_user(db)
    event.add_user(user=limited_user, rights=PermissionRight.READ, session=db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=authentication_token_from_user(db=db, user=limited_user, client=client),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_remove_own_user_from_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    user = create_random_user(db)
    event.add_user(user=user, rights=PermissionRight.MANAGE_USERS, session=db)

    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}/users/{user.id}",
        headers=authentication_token_from_user(db=db, user=user, client=client),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Users are not allowed to delete themselves when they are not an super admin"
