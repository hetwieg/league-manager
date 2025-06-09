from sqlmodel import Session

from app.models.event import Event, EventCreate
from app.tests.utils.utils import random_email, random_lower_string


def create_random_event(db: Session, name: str = None, contact: str = None) -> Event:
    if not name:
        name = random_lower_string()

    if not contact:
        contact = random_email()

    event_in = EventCreate(name=name, contact=contact)
    return Event.create(session=db, create_obj=event_in)
