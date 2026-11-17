import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileCreate(BaseModel):
    """What the client sends to create a profile."""

    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    display_name: str = Field(min_length=1, max_length=50)

    # mode="before" runs BEFORE the length/pattern checks, so "  Alice " becomes
    # "alice" first and is then validated.
    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, v):
        return v.strip() if isinstance(v, str) else v


class ProfilePublic(BaseModel):
    """What the API returns. Only public fields, never anything sensitive."""

    model_config = ConfigDict(from_attributes=True)  # lets it be built from a Profile object

    id: uuid.UUID
    username: str
    display_name: str

