import uuid

from sqlmodel import Field, SQLModel

class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: uuid.UUID = Field(primary_key=True)
    username: str = Field(unique=True, index=True, max_length=30)
    display_name: str = Field(max_length=50)

