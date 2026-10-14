# PLACEHOLDER so the calendar foreign keys have a table to point at.
# Misha owns the real users model -- when it lands, delete this file and keep
# the table name "users" (calendars.owner_id and calendar_shares.user_id point at users.id).

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    display_name: str
    default_timezone: str = "America/New_York"
    created_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None
