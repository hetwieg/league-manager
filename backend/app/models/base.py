from enum import Enum, IntFlag  # Python 3.11 >= StrEnum
from enum import auto as auto_enum
from uuid import UUID as RowId

from sqlmodel import SQLModel

__all__ = [
    "RowId",
    "DocumentedStrEnum",
    "DocumentedIntFlag",
    "auto_enum",
    "ApiTags",
    "BaseSQLModel",
    "Message",
]

# region SQLModel base class ###################################################


class BaseSQLModel(SQLModel):
    pass


# endregion


# region enum # Fields #########################################################


class DocumentedStrEnum(str, Enum):
    pass


class DocumentedIntFlag(IntFlag):
    pass


# #############################################################################


class ApiTags(DocumentedStrEnum):
    LOGIN = "Login"
    USERS = "Users"
    UTILS = "Utils"
    PRIVATE = "Private"

    APIKEY = "APIKey"

    EVENTS = "Events"
    TEAMS = "Teams"


# endregion


# region Generic message #######################################################


class Message(SQLModel):
    message: str


# #############################################################################

# endregion
