from sqlmodel import SQLModel

from uuid import UUID as RowId


# region SQLModel base class ###################################################


class BaseSQLModel(SQLModel):
    pass


# endregion

# region Generic message #######################################################


class Message(SQLModel):
    message: str


# #############################################################################

# endregion
