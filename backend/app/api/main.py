from fastapi import APIRouter

from app.api.routes import (
    events,
    teams,
    associations,
    divisions,
    login,
    private,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)


api_router.include_router(events.router)
api_router.include_router(teams.router)
api_router.include_router(associations.router)
api_router.include_router(divisions.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
