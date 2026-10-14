from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel

Permission = Literal["viewer", "editor"]
Relationship = Literal["close_friend", "friend", "temp"]


class CalendarCreate(SQLModel):
    name: str
    description: str | None = None
    color: str | None = None
    timezone: str = "America/New_York"


class CalendarUpdate(SQLModel):
    # every field optional: PATCH only changes what you send
    name: str | None = None
    description: str | None = None
    color: str | None = None
    timezone: str | None = None


class CalendarRead(SQLModel):
    id: int
    owner_id: int
    name: str
    description: str | None
    color: str | None
    timezone: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    my_access: Literal["owner", "viewer", "editor"]  # what the caller can do


class ShareCreate(SQLModel):
    email: str  # share by email -- that's what the frontend will have
    permission: Permission = "viewer"
    relationship: Relationship | None = None


class ShareRead(SQLModel):
    calendar_id: int
    user_id: int
    email: str
    display_name: str
    permission: Permission
    relationship: Relationship | None
    created_at: datetime
