from datetime import datetime
from typing import Literal

from sqlmodel import SQLModel

FriendLevel = Literal["close", "professional"]
RequestStatus = Literal["pending", "accepted", "declined", "cancelled", "expired"]


class UserBrief(SQLModel):
    id: int
    email: str
    display_name: str


class FriendRequestCreate(SQLModel):
    email: str  # who to send it to -- must already have an account
    level: FriendLevel


class FriendRequestRead(SQLModel):
    id: int
    level: FriendLevel
    status: RequestStatus
    sender: UserBrief
    recipient: UserBrief
    created_at: datetime
    expires_at: datetime
    responded_at: datetime | None


class TokenBody(SQLModel):
    # the token from the email link. sent in the body (not the url) so it doesn't end up in server logs
    token: str


class TokenRespond(TokenBody):
    action: Literal["accept", "decline"]


class FriendRead(SQLModel):
    user: UserBrief
    level: FriendLevel
    since: datetime
