from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models.event import (
    Event,
    EventCreate,
)
from app.models.association import (
    Association,
)
from app.models.division import (
    Division,
)
from app.models.team import (
    Team,
    TeamCreate,
)
from app.models.user import (
    Permission,
    PermissionModule,
    PermissionPart,
    PermissionRight,
    Role,
    User,
    UserCreate,
)
from app.models.apikey import (
    ApiKey,
)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    from app.models.base import BaseSQLModel

    # This works because the models are already imported and registered from app.models
    BaseSQLModel.metadata.create_all(engine)

    # region SuperUser ---------------------------------------------------------

    # Create system admin role
    system_admin_role = session.exec(select(Role).where(Role.name == "Admin")).first()
    if not system_admin_role:
        system_admin_role_in = Role(
            name="Admin",
            is_active=True,
            description="Super admins",
        )
        system_admin_role = Role.create(
            session=session, create_obj=system_admin_role_in
        )

    user_role = session.exec(select(Role).where(Role.name == "User")).first()
    if not user_role:
        user_role_in = Role(
            name="User",
            is_active=True,
            description="Role with only healthcheck read rights",
        )
        user_role = Role.create(session=session, create_obj=user_role_in)

    # init all possible permissions
    existing_permissions = session.exec(select(Permission)).all()

    # Create missing permissions and link to system admin role
    for module in PermissionModule:
        for part in PermissionPart:
            permission = next(
                filter(
                    lambda p: p.module == module and p.part == part,
                    existing_permissions,
                ),
                None,
            )
            if not permission:
                permission_in = Permission(
                    module=module,
                    part=part,
                    is_active=True,
                    description=f"{module.name} - {part.name}",
                )
                permission = Permission.create(
                    session=session, create_obj=permission_in
                )

            system_admin_role.add_permission(
                permission, session=session, right=PermissionRight.ADMIN
            )

            if module == PermissionModule.SYSTEM and part == PermissionPart.HEALTHCHECK:
                user_role.add_permission(
                    permission, session=session, right=PermissionRight.READ
                )

    session.commit()

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_verified=True,
            is_active=True,
        )
        user = User.create(session=session, create_obj=user_in)
    user.add_role(db_obj=system_admin_role, session=session)
    session.commit()

    event = session.exec(
        select(Event).where(Event.contact == settings.FIRST_SUPERUSER)
    ).first()
    if not event:
        event_in = EventCreate(
            contact=settings.FIRST_SUPERUSER,
            is_active=True,
            name="Admins first event",
        )
        event = Event.create(session=session, create_obj=event_in)
    event.add_user(user, PermissionRight.ADMIN, session=session)

    team = session.exec(
        select(Event).where(Team.theme_name == "Laaiend vuur 熾熱的火 🔥")
    ).first()
    if not team:
        team_in = TeamCreate(
            theme_name="Laaiend vuur 熾熱的火 🔥",
            event_id=event.id,
        )
        team = Team.create(session=session, create_obj=team_in)

    session.commit()

    # endregion
