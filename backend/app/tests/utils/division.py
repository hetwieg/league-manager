from sqlmodel import Session

from app.models.association import Association
from app.models.division import Division, DivisionCreate
from app.tests.utils.association import create_random_association
from app.tests.utils.utils import random_lower_string


def create_random_division(db: Session, name: str = None, association: Association = None) -> Division:
    if not name:
        name = random_lower_string()

    if not association:
        association = create_random_association(db)

    division_in = DivisionCreate(name=name, association_id=association.id)
    return Division.create(session=db, create_obj=division_in)
