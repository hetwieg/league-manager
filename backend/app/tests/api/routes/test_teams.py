import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import PermissionRight

from app.core.config import settings
from app.tests.conftest import EventUserHeader
from app.tests.utils.event import create_random_event
from app.tests.utils.team import create_random_team


def test_create_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    event = create_random_event(db)
    data = {
        "theme_name": "Foo",
        "event_id": str(event.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["theme_name"] == data["theme_name"]
    assert content["event_id"] == str(event.id)
    assert "id" in content

def test_create_team_without_event(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "theme_name": "No Event Team",
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "event_id"]


def test_create_team_with_incorrect_event(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "theme_name": "No Event Team",
        "event_id": str(uuid.uuid4()),  # Non-existent event
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"

def test_read_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(team.id)
    assert content["theme_name"] == team.theme_name
    assert content["event_id"] == str(team.event_id)

def test_read_team_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"


def test_read_event_not_enough_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough permissions"


def test_read_team_with_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)

    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=event_user_token_headers.headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(team.id)
    assert content["theme_name"] == team.theme_name
    assert content["event_id"] == str(event_user_token_headers.event.id)


def test_read_teams(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    create_random_team(db)
    create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert isinstance(content["data"], list)
    assert content["count"] >= 2


def test_read_teams_with_normal_user(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    create_random_team(db)
    create_random_team(db)
    response = client.get(
        f"{settings.API_V1_STR}/teams/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 0


def test_read_teams_with_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    create_random_team(db, event=event_user_token_headers.event)

    response = client.get(
        f"{settings.API_V1_STR}/teams/",
        headers=event_user_token_headers.headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert isinstance(content["data"], list)
    assert content["count"] >= 1


def test_update_team_name(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    data = {"theme_name": "Updated Team Name"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(team.id)
    assert content["theme_name"] == data["theme_name"]
    assert content["event_id"] == str(team.event_id)


def test_update_team_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {"theme_name": "Non-existent team"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"


def test_update_team_not_enough_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    data = {"theme_name": "Not enough permissions team"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough permissions"


def test_update_team_name_with_event_permissions(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)
    data = {"theme_name": "Updated Team Name with Event permissions"}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=event_user_token_headers.headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(team.id)
    assert content["theme_name"] == data["theme_name"]
    assert content["event_id"] == str(event_user_token_headers.event.id)


def test_update_team_event(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    new_event = create_random_event(db)

    data = {"event_id": str(new_event.id)}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(team.id)
    assert content["theme_name"] == team.theme_name
    assert content["event_id"] == str(new_event.id)


def test_update_team_event_not_found(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    data = {"event_id": str(uuid.uuid4())}

    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "New event not found"


def test_update_team_event_with_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)

    new_event = create_random_event(db)
    new_event.add_user(user=event_user_token_headers.user, rights=PermissionRight.MANAGE_TEAMS, session=db)

    data = {"event_id": str(new_event.id)}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=event_user_token_headers.headers,
        json=data,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(team.id)
    assert content["theme_name"] == team.theme_name
    assert content["event_id"] == str(new_event.id)


def test_update_team_event_with_event_user_not_enough_permissions(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)

    new_event = create_random_event(db)

    data = {"event_id": str(new_event.id)}
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=event_user_token_headers.headers,
        json=data,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Team deleted successfully"


def test_delete_team_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"


def test_delete_not_enough_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_team_with_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}",
        headers=event_user_token_headers.headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Team deleted successfully"
