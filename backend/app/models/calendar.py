import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class Calendar(SQLModel, table=True):
    __tablename__ = "calendars"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    name: str
    description: str | None = None
    color: str | None = None
    timezone: str = "America/New_York"
    is_primary: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None


class CalendarShare(SQLModel, table=True):
    __tablename__ = "calendar_shares"

    calendar_id: int = Field(foreign_key="calendars.id", primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="profiles.id", primary_key=True)
    permission: str = "viewer"
    relationship: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
