import random

from sqlmodel import Session

from app.models.event import Event
from app.models.team import Team, TeamCreate

from app.tests.utils.event import create_random_event
from app.tests.utils.utils import random_lower_string


def random_short_name() -> str:
    return str(random.Random().randrange(1, 200))

def create_random_team(db: Session, event: Event | None = None) -> Team:
    name = random_lower_string()
    short_name = random_short_name()

    if not event:
        event = create_random_event(db)

    team_in = TeamCreate(theme_name=name, short_name=short_name, event_id=event.id)
    team = Team.create(session=db, create_obj=team_in)
    return team
