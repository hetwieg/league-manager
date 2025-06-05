import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete, func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_system_admin,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.base import Message, RowId
from app.models.user import (
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    PermissionModule,
    PermissionPart,
    PermissionRight,
)
from app.models.apikey import (
    ApiKey,
    ApiKeyCreate,
    ApiKeyPublic,
    ApiKeysPublic,
    ApiKeyGenerate,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_system_admin)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_system_admin)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = User.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = User.create(session=session, create_obj=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = User.get_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me/api-key", response_model=ApiKeysPublic)
def read_apikey_me(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve api keys from user
    """

    count_statement = (
        select(func.count())
        .select_from(ApiKey)
        .where(ApiKey.user_id == current_user.id)
    )
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    api_keys = session.exec(statement).all()

    return ApiKeysPublic(data=api_keys, count=count)


@router.post("/me/api-key", response_model=ApiKeyPublic)
def create_apikey_met(
    *, session: SessionDep, body: ApiKeyGenerate, current_user: CurrentUser
) -> Any:
    """
    Generate a new api-key.
    """

    data_obj = body.model_dump(exclude_unset=True)
    extra_data = {
        "user_id": current_user.id,
    }
    create_obj = ApiKeyCreate.model_validate(data_obj, update=extra_data)

    api_key = ApiKey.create(session=session, create_obj=create_obj)
    current_user.api_keys.append(api_key)
    session.add(current_user)
    session.commit()
    return api_key


@router.delete("/me/api-key/{api_key}", response_model=ApiKeyPublic)
def delete_apikey_me(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    api_key: RowId,
) -> Message:
    """
    Delete a api-key.
    """

    for api_key in current_user.api_keys:
        if api_key.id == api_key:
            session.delete(api_key)
            session.commit()
            return Message(message="Api key deleted successfully")

    raise HTTPException(status_code=404, detail="API key not found")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.has_permission(
        module=PermissionModule.SYSTEM,
        part=PermissionPart.ADMIN,
        rights=PermissionRight.DELETE,
    ):
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = User.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = User.create(session=session, create_obj=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.has_permission(module=PermissionModule.USER, part=PermissionPart.ADMIN, rights=PermissionRight.READ):
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_system_admin)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = User.get_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = User.update(session=session, db_obj=db_user, in_obj=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_system_admin)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    # statement = delete(Item).where(col(Item.owner_id) == user_id)
    # session.exec(statement)  # type: ignore
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")
