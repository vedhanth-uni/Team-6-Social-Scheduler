from datetime import datetime

from pydantic import NaiveDatetime
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    calendar_id: int = Field(foreign_key="calendars.id", index=True)
    created_by: int = Field(foreign_key="users.id")
    title: str
    description: str | None = None
    location: str | None = None
    all_day: bool = False

    # local time not utc so a 9am class doesnt turn into 8am after dst
    start_local: NaiveDatetime
    end_local: NaiveDatetime
    timezone: str = "America/New_York"

    # public, professional or private
    visibility: str = "private"

    # how it repeats, none if its a one time thing
    rrule: str | None = None

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None  # soft delete like calendars


class Attendee(SQLModel, table=True):
    __tablename__ = "attendees"
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)  # cant join the same event twice

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    email: str | None = None  # for people without an account
    rsvp_status: str = "accepted"
    is_organizer: bool = False
    is_optional: bool = False
    responded_at: datetime | None = Field(default_factory=utcnow)
