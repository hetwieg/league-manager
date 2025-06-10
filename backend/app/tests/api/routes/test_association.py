import uuid

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.association import create_random_association


def test_create_association(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    data = {
        "name": "Scouting Maurits-Viool",
        "contact": "Sebas",
        "scouting_id": "2577",
    }
    response = client.post(
        f"{settings.API_V1_STR}/associations/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert content["scouting_id"] == data["scouting_id"]
    assert "id" in content


def test_create_association_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    data = {
        "name": "Scouting Maurits-Viool",
        "contact": "Sebas",
        "scouting_id": "2577",
    }
    response = client.post(
        f"{settings.API_V1_STR}/associations/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_association(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    response = client.get(
        f"{settings.API_V1_STR}/associations/{association.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["id"] == str(association.id)
    assert content["name"] == association.name
    assert content["contact"] == association.contact
    assert content["scouting_id"] == association.scouting_id


def test_read_association_not_found(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/associations/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Association not found"


def test_read_association_no_permission(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    response = client.get(
        f"{settings.API_V1_STR}/associations/{association.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_read_associations(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    create_random_association(db)
    create_random_association(db)
    response = client.get(
        f"{settings.API_V1_STR}/associations/",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] >= 2
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) <= content["count"]


def test_read_associations_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    create_random_association(db)
    create_random_association(db)
    response = client.get(
        f"{settings.API_V1_STR}/associations/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert "count" in content
    assert content["count"] == 0
    assert "data" in content
    assert isinstance(content["data"], list)
    assert len(content["data"]) == 0


def test_update_association(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    data = {
        "name": "Updated name",
        "contact": "Updated contact",
    }
    response = client.put(
        f"{settings.API_V1_STR}/associations/{association.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["id"] == str(association.id)
    assert content["name"] == data["name"]
    assert content["contact"] == data["contact"]
    assert content["scouting_id"] == association.scouting_id


def test_update_association_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {
        "name": "Not found",
        "contact": "Not found",
    }
    response = client.put(
        f"{settings.API_V1_STR}/associations/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Association not found"


def test_update_association_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    data = {
        "name": "No permissions",
        "contact": "No permissions",
    }
    response = client.put(
        f"{settings.API_V1_STR}/associations/{association.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"


def test_delete_association(client: TestClient, superuser_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    response = client.delete(
        f"{settings.API_V1_STR}/associations/{association.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Association deleted successfully"


def test_delete_association_not_found(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/associations/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Association not found"


def test_delete_association_no_permissions(client: TestClient, normal_user_token_headers: dict[str, str], db: Session) -> None:
    association = create_random_association(db)
    response = client.delete(
        f"{settings.API_V1_STR}/associations/{association.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Not enough permissions"
