import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

FriendLevel = Literal["close", "professional"]


class ProfileBrief(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str


class FriendRequestCreate(BaseModel):
    username: str
    level: FriendLevel

    @field_validator("username", mode="before")
    @classmethod
    def normalize(cls, v):
        return v.strip().lower().lstrip("@") if isinstance(v, str) else v


class FriendRequestRead(BaseModel):
    id: int
    level: str
    status: Literal["pending", "accepted", "declined"]
    sender: ProfileBrief
    recipient: ProfileBrief
    created_at: datetime


class RespondBody(BaseModel):
    # the email link carries the request id. being logged in as the recipient is what protects it
    token: str
    action: Literal["accept", "decline"]


class LookupBody(BaseModel):
    token: str


class FriendRead(BaseModel):
    user: ProfileBrief
    level: str
    since: datetime
