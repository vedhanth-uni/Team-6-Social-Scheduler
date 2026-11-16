import uuid
from datetime import datetime

from pydantic import NaiveDatetime
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    calendar_id: int = Field(foreign_key="calendars.id", index=True)
    created_by: uuid.UUID = Field(foreign_key="profiles.id")
    title: str
    description: str | None = None
    location: str | None = None
    all_day: bool = False
    start_local: NaiveDatetime
    end_local: NaiveDatetime
    timezone: str = "America/New_York"
    visibility: str = "private"
    rrule: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None


class Attendee(SQLModel, table=True):
    __tablename__ = "attendees"
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="profiles.id", index=True)
    rsvp_status: str = "accepted"
    responded_at: datetime | None = Field(default_factory=utcnow)
