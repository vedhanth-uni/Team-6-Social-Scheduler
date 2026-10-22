from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel

Visibility = Literal["public", "professional", "private"]


class EventCreate(SQLModel):
    title: str
    description: str | None = None
    location: str | None = None
    all_day: bool = False
    # works with or without a timezone offset
    start: datetime
    end: datetime | None = None  # not needed for all day events
    timezone: str | None = None  # uses the calendars timezone if empty
    visibility: Visibility = "private"
    rrule: str | None = None


class EventUpdate(SQLModel):
    # only updates what you send
    title: str | None = None
    description: str | None = None
    location: str | None = None
    all_day: bool | None = None
    start: datetime | None = None
    end: datetime | None = None
    timezone: str | None = None
    visibility: Visibility | None = None
    rrule: str | None = None


class EventRead(SQLModel):
    id: int
    calendar_id: int
    created_by: int
    title: str
    description: str | None
    location: str | None
    all_day: bool
    start: datetime
    end: datetime
    timezone: str
    visibility: Visibility
    rrule: str | None
    can_edit: bool
    joined: bool


class Occurrence(SQLModel):
    event_id: int
    title: str
    start: datetime
    end: datetime
    all_day: bool
    is_recurring: bool
    visibility: Visibility
    joined: bool
