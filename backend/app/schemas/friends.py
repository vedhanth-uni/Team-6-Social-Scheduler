import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.profile import ProfilePublic


class FriendRequestCreate(BaseModel):
    receiver_id: uuid.UUID


class FriendLevelUpdate(BaseModel):
    # Keep in sync with LEVEL_* constants in the model.
    level: Literal["regular", "close"]


class FriendOut(BaseModel):
    friend: ProfilePublic
    level: str


class FriendRequestOut(BaseModel):
    id: int                    # what accept/reject endpoints take
    user: ProfilePublic        # the OTHER person
    status: str
    created_at: datetime


class FriendsOverview(BaseModel):
    friend_count: int
    friends: list[FriendOut]
    incoming_requests: list[FriendRequestOut]
    outgoing_requests: list[FriendRequestOut]