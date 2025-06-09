import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.user import PermissionRight
from app.tests.utils.event import create_random_event
from app.tests.utils.user import create_random_user, authentication_token_from_user


def test_create_event(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {"name": "Foo", "contact": "Someone"}

    response = client.post(
        f"{settings.API_V1_STR}/events/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert "id" in content
    assert "is_active" in content
    assert "start_at" in content
    assert "end_at" in content


def test_read_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
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
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Event not found"


def test_read_event_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.get(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_events(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_event(db)
    create_random_event(db)
    response = client.get(
        f"{settings.API_V1_STR}/events/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    data = {"name": "Updated name", "contact": "Updated contact"}
    response = client.put(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
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
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Event not found"


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
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_event(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    event = create_random_event(db)
    response = client.delete(
        f"{settings.API_V1_STR}/events/{event.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Event deleted successfully"


def test_delete_event_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/events/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
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
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


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
    assert response.status_code == 200
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
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


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
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


# TODO: Add user (super, less rights, own rights, more rights) (*** user without rights)
# TODO: Edit user rights (super, less rights, own rights, more rights) (*** user without rights)
# TODO: Remove user (*** user without rights)
# TODO: Remove own user (is allowed)
# TODO: Remove not linked user
