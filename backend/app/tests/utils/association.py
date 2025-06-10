from sqlmodel import Session

from app.models.association import Association, AssociationCreate
from app.tests.utils.utils import random_lower_string


def create_random_association(db: Session, name: str = None) -> Association:
    if not name:
        name = random_lower_string()

    association_in = AssociationCreate(name=name)
    return Association.create(session=db, create_obj=association_in)
