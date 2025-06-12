import uuid

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.division import DivisionTeamLink, DivisionTeamLinkCreate
from app.tests.conftest import EventUserHeader
from app.tests.utils.division import create_random_division
from app.tests.utils.association import create_random_association
from app.tests.utils.team import create_random_team
from app.tests.utils.utils import random_lower_string


def test_create_division(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    data = {
        "name": "Verkenners",
        "scouting_id": "122314",
        "association_id": str(association.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/divisions/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["scouting_id"] == data["scouting_id"]
    assert content["association_id"] == str(association.id)
    assert "contact" in content
    assert "id" in content


def test_create_division_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    data = {
        "name": "Padvinsters",
        "contact": "-",
        "scouting_id": "122323",
        "association_id": str(association.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/divisions/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_division(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    response = client.get(
        f"{settings.API_V1_STR}/divisions/{division.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["id"] == str(division.id)
    assert content["name"] == division.name
    assert content["contact"] == division.contact
    assert content["scouting_id"] == division.scouting_id
    assert content["association_id"] == str(division.association_id)


def test_read_division_not_found(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/divisions/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Division not found"


def test_read_division_no_permission(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    response = client.get(
        f"{settings.API_V1_STR}/divisions/{division.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_divisions(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    create_random_division(db)
    create_random_division(db)
    response = client.get(
        f"{settings.API_V1_STR}/divisions/",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] >= 2
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) <= content["count"]


def test_read_divisions_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    create_random_division(db)
    create_random_division(db)
    response = client.get(
        f"{settings.API_V1_STR}/divisions/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] == 0
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) == 0


def test_update_division(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    data = {
        "name": "Updated name",
        "contact": "Updated contact",
    }
    response = client.put(
        f"{settings.API_V1_STR}/divisions/{division.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["id"] == str(division.id)
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert content["scouting_id"] == division.scouting_id
    assert content["association_id"] == str(division.association_id)


def test_update_division_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "name": "Not found",
        "contact": "Not found",
    }
    response = client.put(
        f"{settings.API_V1_STR}/divisions/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Division not found"


def test_update_division_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    data = {
        "name": "No permissions",
        "contact": "No permissions",
    }
    response = client.put(
        f"{settings.API_V1_STR}/divisions/{division.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_division(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    response = client.delete(
        f"{settings.API_V1_STR}/divisions/{division.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Division deleted successfully"


def test_delete_division_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/divisions/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Division not found"


def test_delete_division_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    response = client.delete(
        f"{settings.API_V1_STR}/divisions/{division.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_create_team_division_link(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    division = create_random_division(db)
    data = {
        "name": "Otters",
        "division_id": str(division.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["team_id"] == str(team.id)
    assert content["division_id"] == str(division.id)


def test_create_team_division_link_unknown_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    division = create_random_division(db)
    data = {
        "name": "Vossen",
        "division_id": str(division.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}/division",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Team not found"


def test_create_team_division_already_linked(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    division1 = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division1.id), team=team)

    division2 = create_random_division(db)
    data = {
        "name": "Vossen",
        "division_id": str(division2.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Team already linked to division"


def test_create_team_division_link_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)
    division = create_random_division(db)
    data = {
        "name": "Arenden",
        "division_id": str(division.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_create_team_division_link_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)
    division = create_random_division(db)
    data = {
        "name": "Sperwers",
        "division_id": str(division.id),
    }
    response = client.post(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=event_user_token_headers.headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["team_id"] == str(team.id)
    assert content["division_id"] == str(division.id)


def test_read_team_division(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == name
    assert content["team_id"] == str(team.id)
    assert content["division_id"] == str(division.id)


def test_read_team_division_unknown_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}/division",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Team not found"


def test_read_team_division_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_team_division_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    response = client.get(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=event_user_token_headers.headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == name
    assert content["team_id"] == str(team.id)
    assert content["division_id"] == str(division.id)


def test_update_team_division_link(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    data = {
        "name": "Muizenoor",
    }
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["team_id"] == str(team.id)
    assert content["division_id"] == str(division.id)


def test_update_team_division_link_unknown_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    data = {
        "name": "Leeuenbek",
    }
    response = client.put(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}/division",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Team not found"


def test_update_team_division_link_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    data = {
        "name": "Geitebaard",
    }
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_update_team_division_link_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    data = {
        "name": "Berenklouw",
    }
    response = client.put(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=event_user_token_headers.headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["team_id"] == str(team.id)
    assert content["division_id"] == str(division.id)


def test_delete_team_division_link(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Division deleted from team successfully"


def test_delete_team_division_link_unknown_team(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/teams/{uuid.uuid4()}/division",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Team not found"


def test_delete_team_division_link_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    team = create_random_team(db)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_team_division_link_event_user(client: TestClient, event_user_token_headers: EventUserHeader, db: Session) -> None:
    team = create_random_team(db, event=event_user_token_headers.event)

    division = create_random_division(db)
    name = random_lower_string()
    DivisionTeamLink.create(session=db, create_obj=DivisionTeamLinkCreate(name=name, division_id=division.id), team=team)

    response = client.delete(
        f"{settings.API_V1_STR}/teams/{team.id}/division",
        headers=event_user_token_headers.headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Division deleted from team successfully"
