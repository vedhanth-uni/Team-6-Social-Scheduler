# Our own users table. Every other table points at users.id (an int), while Supabase identifies
# people by a uuid -- auth_id holds that uuid (the token's "sub") and is how a login finds its row.
# Rows are created automatically the first time someone logs in (see app/auth.py).

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    auth_id: str | None = Field(default=None, unique=True, index=True)  # supabase auth.users.id
    email: str = Field(unique=True, index=True)
    display_name: str
    default_timezone: str = "America/New_York"
    created_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = None
