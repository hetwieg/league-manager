from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app.core.security import verify_password
from app.models.user import (
    PermissionModule,
    PermissionPart,
    User,
    UserCreate,
    UserUpdate,
)
from app.tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = User.create(session=db, create_obj=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = User.create(session=db, create_obj=user_in)
    authenticated_user = User.authenticate(session=db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = User.authenticate(session=db, email=email, password=password)
    assert user is None


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = User.create(session=db, create_obj=user_in)
    assert user.is_active is True


def test_check_if_user_is_active_inactive(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    user = User.create(session=db, create_obj=user_in)
    assert user.is_active is False


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = User.create(session=db, create_obj=user_in)
    user.add_role(name="Admin", session=db)
    assert (
        user.has_permission(module=PermissionModule.SYSTEM, part=PermissionPart.ADMIN)
        is True
    )


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = User.create(session=db, create_obj=user_in)
    user.add_role(name="User", session=db)
    assert (
        user.has_permission(module=PermissionModule.SYSTEM, part=PermissionPart.ADMIN)
        is False
    )


def test_get_user(db: Session) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password)
    user = User.create(session=db, create_obj=user_in)
    user.add_role(name="Admin", session=db)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password)
    user = User.create(session=db, create_obj=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password)
    if user.id is not None:
        User.update(session=db, db_obj=user, in_obj=user_in_update)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert verify_password(new_password, user_2.hashed_password)
