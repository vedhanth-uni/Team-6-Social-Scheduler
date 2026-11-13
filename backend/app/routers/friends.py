# friend requests + friends list
#
#   POST   /friend-requests                    send one (emails the other person)
#   GET    /friend-requests?direction=...      my pending incoming / outgoing requests
#   POST   /friend-requests/{id}/accept        accept from inside the app
#   POST   /friend-requests/{id}/decline       decline from inside the app
#   DELETE /friend-requests/{id}               sender cancels their own pending request
#   POST   /friend-requests/lookup             see what an email link is for (frontend landing page)
#   POST   /friend-requests/respond            accept/decline using the token from the email link
#   GET    /friends                            my friends + level
#   DELETE /friends/{user_id}                  unfriend (works from either side)
#
# every endpoint needs a logged in user (current_user), including the email link ones. clicking the
# link in the email opens the frontend, which logs you in first if needed, then calls /respond.
# the token alone is not enough -- you also have to be logged in as the person it was sent to.
#
# a connection is never updated, only created or deleted (see models/friend.py for why)

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth import current_user
from app.config import settings
from app.database import get_session
from app.models.friend import FriendRequest, Friendship, pair
from app.models.timeutil import utcnow
from app.models.user import User
from app.schemas.friend import (
    FriendRead,
    FriendRequestCreate,
    FriendRequestRead,
    TokenBody,
    TokenRespond,
    UserBrief,
)
from app.services.email import send_email
from app.services.friend_emails import friend_request_email, request_accepted_email

router = APIRouter(tags=["Friends"])


# ---------- helpers ----------

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def as_utc(dt: datetime) -> datetime:
    # sqlite hands datetimes back without a timezone even though we saved them in utc
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def is_expired(req: FriendRequest) -> bool:
    return as_utc(req.expires_at) <= utcnow()


def live_status(req: FriendRequest) -> str:
    # expired requests stay "pending" in the db, we just report them as expired
    return "expired" if req.status == "pending" and is_expired(req) else req.status


def brief(u: User) -> UserBrief:
    return UserBrief(id=u.id, email=u.email, display_name=u.display_name)


def to_read(req: FriendRequest, session: Session) -> FriendRequestRead:
    return FriendRequestRead(
        id=req.id,
        level=req.level,
        status=live_status(req),
        sender=brief(session.get(User, req.sender_id)),
        recipient=brief(session.get(User, req.recipient_id)),
        created_at=req.created_at,
        expires_at=req.expires_at,
        responded_at=req.responded_at,
    )


def get_friendship(a: int, b: int, session: Session) -> Friendship | None:
    return session.get(Friendship, pair(a, b))


def open_request_between(a: int, b: int, session: Session) -> FriendRequest | None:
    """A pending, not-expired request between a and b in either direction."""
    rows = session.exec(
        select(FriendRequest).where(
            FriendRequest.status == "pending",
            or_(
                (FriendRequest.sender_id == a) & (FriendRequest.recipient_id == b),
                (FriendRequest.sender_id == b) & (FriendRequest.recipient_id == a),
            ),
        )
    ).all()
    return next((r for r in rows if not is_expired(r)), None)


def respond(req: FriendRequest, user: User, action: Literal["accept", "decline"],
            session: Session, background: BackgroundTasks) -> FriendRequestRead:
    """Shared by the in-app buttons and the email link. Caller already checked user is the recipient."""
    if req.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"This request was already {req.status}")
    if is_expired(req):
        raise HTTPException(status.HTTP_410_GONE, "This request has expired. Ask them to send a new one.")

    sender = session.get(User, req.sender_id)
    if sender is None or sender.deleted_at is not None:
        raise HTTPException(status.HTTP_410_GONE, "The person who sent this request no longer has an account")

    req.responded_at = utcnow()

    if action == "decline":
        req.status = "declined"  # sender is not told
        session.add(req)
        session.commit()
        session.refresh(req)
        return to_read(req, session)

    if get_friendship(req.sender_id, req.recipient_id, session):
        raise HTTPException(status.HTTP_409_CONFLICT, "You're already friends")

    low, high = pair(req.sender_id, req.recipient_id)
    req.status = "accepted"
    session.add(req)
    session.add(Friendship(user_low_id=low, user_high_id=high, level=req.level, request_id=req.id))
    try:
        session.commit()
    except IntegrityError:
        # two accepts racing each other -- the primary key on friendships caught it
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You're already friends")
    session.refresh(req)

    background.add_task(send_email, request_accepted_email(
        to=sender.email, accepter_name=user.display_name, level=req.level,
    ))
    return to_read(req, session)


def load_by_token(token: str, user: User, session: Session) -> FriendRequest:
    req = session.exec(select(FriendRequest).where(FriendRequest.token_hash == hash_token(token))).first()
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This link is invalid")
    if req.recipient_id != user.id:
        # most likely logged into a different account than the one the email went to
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "This request was sent to a different account. Log in with that account to respond.")
    return req


# ---------- requests ----------

@router.post("/friend-requests", response_model=FriendRequestRead, status_code=status.HTTP_201_CREATED)
def send_request(
    body: FriendRequestCreate,
    background: BackgroundTasks,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    email = body.email.strip()
    target = session.exec(
        select(User).where(User.email == email, User.deleted_at == None)  # noqa: E711
    ).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user with that email exists")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't send a friend request to yourself")
    if get_friendship(user.id, target.id, session):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "You're already friends. To change the level, remove them and send a new request.")

    existing = open_request_between(user.id, target.id, session)
    if existing and existing.sender_id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already sent them a request")
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"{target.display_name} already sent you a request. Accept or decline that one instead.")

    token = secrets.token_urlsafe(32)
    req = FriendRequest(
        sender_id=user.id,
        recipient_id=target.id,
        level=body.level,
        token_hash=hash_token(token),
        expires_at=utcnow() + timedelta(days=settings.FRIEND_REQUEST_TTL_DAYS),
    )
    session.add(req)
    session.commit()
    session.refresh(req)

    background.add_task(send_email, friend_request_email(
        to=target.email,
        sender_name=user.display_name,
        sender_email=user.email,
        level=req.level,
        token=token,
        ttl_days=settings.FRIEND_REQUEST_TTL_DAYS,
    ))
    return to_read(req, session)


@router.get("/friend-requests", response_model=list[FriendRequestRead])
def list_requests(
    direction: Literal["incoming", "outgoing"] = Query("incoming"),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """Pending requests that can still be answered."""
    col = FriendRequest.recipient_id if direction == "incoming" else FriendRequest.sender_id
    rows = session.exec(
        select(FriendRequest)
        .where(col == user.id, FriendRequest.status == "pending")
        .order_by(FriendRequest.created_at.desc())
    ).all()
    return [to_read(r, session) for r in rows if not is_expired(r)]


def load_incoming(req_id: int, user: User, session: Session) -> FriendRequest:
    req = session.get(FriendRequest, req_id)
    if req is None or req.recipient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")
    return req


@router.post("/friend-requests/{req_id}/accept", response_model=FriendRequestRead)
def accept_request(
    req_id: int,
    background: BackgroundTasks,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    return respond(load_incoming(req_id, user, session), user, "accept", session, background)


@router.post("/friend-requests/{req_id}/decline", response_model=FriendRequestRead)
def decline_request(
    req_id: int,
    background: BackgroundTasks,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    return respond(load_incoming(req_id, user, session), user, "decline", session, background)


@router.delete("/friend-requests/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_request(
    req_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    req = session.get(FriendRequest, req_id)
    if req is None or req.sender_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")
    if req.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"This request was already {req.status}")
    req.status = "cancelled"
    req.responded_at = utcnow()
    session.add(req)
    session.commit()


@router.post("/friend-requests/lookup", response_model=FriendRequestRead)
def lookup_by_token(
    body: TokenBody,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """What the email link points at -- lets the landing page show who it's from before/after responding."""
    return to_read(load_by_token(body.token, user, session), session)


@router.post("/friend-requests/respond", response_model=FriendRequestRead)
def respond_by_token(
    body: TokenRespond,
    background: BackgroundTasks,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    return respond(load_by_token(body.token, user, session), user, body.action, session, background)


# ---------- friends ----------

@router.get("/friends", response_model=list[FriendRead])
def list_friends(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(Friendship).where(or_(Friendship.user_low_id == user.id, Friendship.user_high_id == user.id))
    ).all()
    out = []
    for f in rows:
        other = session.get(User, f.user_high_id if f.user_low_id == user.id else f.user_low_id)
        if other is None or other.deleted_at is not None:
            continue
        out.append(FriendRead(user=brief(other), level=f.level, since=f.created_at))
    out.sort(key=lambda f: f.user.display_name.lower())
    return out


@router.delete("/friends/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    user_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    f = get_friendship(user.id, user_id, session)
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "You're not friends with that user")
    session.delete(f)
    session.commit()
