# friend requests + friendships
#
# a friendship is mutual and has ONE level for both people:
#   close        -> will see the whole calendar except private events (visibility rules come later)
#   professional -> will only see events labeled professional
# "temp" is NOT a level, its a time-limited modifier on top of either one (comes later with visibility)
#
# rules (enforced in routers/friends.py):
#   - only one pending request between two people at a time, in either direction
#   - no new request if you're already friends
#   - a friendship is never updated, only deleted. to change the level, unfriend and send a new request.
#     this is what stops "i accept yours as professional, an hour later you accept mine as close" from
#     silently overwriting the connection.

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.timeutil import utcnow


class FriendRequest(SQLModel, table=True):
    __tablename__ = "friend_requests"

    id: int | None = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="users.id", index=True)
    recipient_id: int = Field(foreign_key="users.id", index=True)
    level: str  # close | professional, picked by the sender
    status: str = "pending"  # pending | accepted | declined | cancelled

    # the email link carries a random token, we only store its sha256 so a db leak
    # doesn't hand out working accept links
    token_hash: str = Field(unique=True, index=True)

    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime
    responded_at: datetime | None = None


class Friendship(SQLModel, table=True):
    __tablename__ = "friendships"

    # stored as an ordered pair (smaller id first) so (alice, bob) and (bob, alice) are the
    # same row -> the primary key itself makes duplicate friendships impossible
    user_low_id: int = Field(foreign_key="users.id", primary_key=True)
    user_high_id: int = Field(foreign_key="users.id", primary_key=True)
    level: str  # close | professional
    request_id: int | None = Field(default=None, foreign_key="friend_requests.id")
    created_at: datetime = Field(default_factory=utcnow)


def pair(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)
