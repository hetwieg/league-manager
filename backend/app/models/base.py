import re

from enum import Enum, IntFlag  # Python 3.11 >= StrEnum
from enum import auto as auto_enum
from uuid import UUID as RowId

from sqlmodel import SQLModel
from sqlalchemy.orm import declared_attr

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
    # Generate __tablename__ automatically with snake_case
    # noinspection PyMethodParameters
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        rx = re.compile(r"(?<=.)(((?<![A-Z])[A-Z])|([A-Z](?=[a-z])))")
        return rx.sub("_\\1", cls.__name__).lower()

# endregion


# region enum # Fields #########################################################


class DocumentedStrEnum(str, Enum):
    pass


class DocumentedIntFlag(IntFlag):
    # TODO: Build DB sport to proper store flags and make it possible to store all mutations
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
    ASSOCIATIONS = "Associations"
    DIVISIONS = "Divisions"


# endregion


# region Generic message #######################################################


class Message(SQLModel):
    message: str


# #############################################################################

# endregion
