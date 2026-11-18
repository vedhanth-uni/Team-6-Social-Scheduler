import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

#IF SOMEONE IS SEEING THIS 😳

class ProfileUpdate(BaseModel):
    """What the client sends to change their profile. Send only what you want to change."""

    username: str | None = Field(default=None, min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    display_name: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v):
        return v.strip().lower().lstrip("@") if isinstance(v, str) else v

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, v):
        return v.strip() if isinstance(v, str) else v


class ProfilePublic(BaseModel):
    """What the API returns about other people. Only public fields, never anything sensitive."""

    model_config = ConfigDict(from_attributes=True)  # lets it be built from a Profile object

    id: uuid.UUID
    username: str
    display_name: str
