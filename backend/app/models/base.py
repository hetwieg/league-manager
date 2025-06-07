from enum import Enum, IntFlag  # Python 3.11 >= StrEnum
from enum import auto as auto_enum
from uuid import UUID as RowId

from sqlmodel import SQLModel

__all__ = [
    "RowId",
    "DocumentedStrEnum",
    "DocumentedIntFlag",
    "auto_enum",
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


# endregion


# region Generic message #######################################################


class Message(SQLModel):
    message: str


# #############################################################################

# endregion
