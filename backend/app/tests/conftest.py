from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models.event import Event
from app.models.user import User, PermissionRight
from app.tests.utils.event import create_random_event
from app.tests.utils.user import authentication_token_from_email, create_random_user
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


class EventUserHeader:
    def __init__(self, user: User,  event: Event, headers: dict[str, str]) -> None:
        self.user = user
        self.event = event
        self.headers = headers


@pytest.fixture(scope="module")
def event_user_token_headers(client: TestClient, db: Session) -> EventUserHeader:
    user = create_random_user(db)
    event = create_random_event(db, name="Test event for user", contact=str(user.email))
    event.add_user(user=user, rights=PermissionRight.ADMIN, session=db)
    headers = authentication_token_from_email(client=client, email=str(user.email), db=db)

    return EventUserHeader(user, event, headers)
