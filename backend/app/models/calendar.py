from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class Calendar(SQLModel, table=True):
    __tablename__ = "calendars"

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)  # who controls it
    name: str
    description: str | None = None
    color: str | None = None
    timezone: str = "America/New_York"  # default tz for events created in it
    is_primary: bool = False  # the user's default calendar
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None  # soft delete


class CalendarShare(SQLModel, table=True):
    __tablename__ = "calendar_shares"

    # (calendar_id, user_id) is the primary key -> a calendar can't be shared
    # with the same person twice; re-sharing just updates the row.
    calendar_id: int = Field(foreign_key="calendars.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)  # person receiving access
    permission: str = "viewer"  # viewer | editor  -> what they can DO
    relationship: str | None = None  # close_friend | friend | temp -> who they ARE to you
    created_at: datetime = Field(default_factory=utcnow)
