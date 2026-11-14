# friend requests + friends list, on the friendships table
#
#   POST   /friend-requests                    send one by username (emails the other person)
#   GET    /friend-requests?direction=...      my pending incoming / outgoing requests
#   POST   /friend-requests/{id}/accept        accept
#   POST   /friend-requests/{id}/decline       decline, deletes the row
#   DELETE /friend-requests/{id}               sender cancels their pending request
#   POST   /friend-requests/lookup             what an email link is for (frontend landing page)
#   POST   /friend-requests/respond            accept/decline from the email link
#   GET    /friends                            my friends + level
#   DELETE /friends/{profile_id}               unfriend, works from either side
#
# one row per pair. pending turns into accepted, declining or unfriending deletes the row.
# to change the level you unfriend and send a new request.

import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth_profile import current_profile
from app.database import get_session
from app.models.friendships import STATUS_ACCEPTED, STATUS_PENDING, Friendship
from app.models.profile import Profile
from app.models.profile_email import ProfileEmail
from app.schemas.friend import (
    FriendRead,
    FriendRequestCreate,
    FriendRequestRead,
    LookupBody,
    ProfileBrief,
    RespondBody,
)
from app.services.email import send_email
from app.services.friend_emails import friend_request_email, request_accepted_email

router = APIRouter(tags=["Friends"])


def brief(p: Profile) -> ProfileBrief:
    return ProfileBrief(id=p.id, username=p.username, display_name=p.display_name)


def to_read(row: Friendship, session: Session, status_override: str | None = None) -> FriendRequestRead:
    return FriendRequestRead(
        id=row.id,
        level=row.level,
        status=status_override or row.status,
        sender=brief(session.get(Profile, row.sender_id)),
        recipient=brief(session.get(Profile, row.reciever_id)),
        created_at=row.created_at,
    )


def email_of(profile_id: uuid.UUID, session: Session) -> str | None:
    row = session.get(ProfileEmail, profile_id)
    return row.email if row else None


def row_between(a: uuid.UUID, b: uuid.UUID, session: Session) -> Friendship | None:
    return session.exec(
        select(Friendship).where(
            or_(
                (Friendship.sender_id == a) & (Friendship.reciever_id == b),
                (Friendship.sender_id == b) & (Friendship.reciever_id == a),
            )
        )
    ).first()


def load_incoming(req_id: int, me: Profile, session: Session) -> Friendship:
    row = session.get(Friendship, req_id)
    if row is None or row.reciever_id != me.id or row.status != STATUS_PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")
    return row


def parse_link_id(token: str) -> int:
    try:
        return int(token)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This link is invalid")


def respond(row: Friendship, me: Profile, action: Literal["accept", "decline"],
            session: Session, background: BackgroundTasks) -> FriendRequestRead:
    if action == "decline":
        out = to_read(row, session, "declined")
        session.delete(row)
        session.commit()
        return out

    row.status = STATUS_ACCEPTED
    session.add(row)
    session.commit()
    session.refresh(row)

    to = email_of(row.sender_id, session)
    if to:
        background.add_task(send_email, request_accepted_email(
            to=to, accepter_name=me.display_name, level=row.level,
        ))
    return to_read(row, session)


@router.post("/friend-requests", response_model=FriendRequestRead, status_code=status.HTTP_201_CREATED)
def send_request(
    body: FriendRequestCreate,
    background: BackgroundTasks,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    target = session.exec(select(Profile).where(Profile.username == body.username)).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user with that username")
    if target.id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't send a friend request to yourself")

    existing = row_between(me.id, target.id, session)
    if existing and existing.status == STATUS_ACCEPTED:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "You're already friends. To change the level, remove them and send a new request.")
    if existing and existing.sender_id == me.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already sent them a request")
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"{target.display_name} already sent you a request. Accept or decline that one instead.")

    row = Friendship(sender_id=me.id, reciever_id=target.id, level=body.level)
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You already sent them a request")
    session.refresh(row)

    to = email_of(target.id, session)
    if to:
        background.add_task(send_email, friend_request_email(
            to=to, sender_name=me.display_name, sender_username=me.username,
            level=row.level, request_id=row.id,
        ))
    return to_read(row, session)


@router.get("/friend-requests", response_model=list[FriendRequestRead])
def list_requests(
    direction: Literal["incoming", "outgoing"] = Query("incoming"),
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    col = Friendship.reciever_id if direction == "incoming" else Friendship.sender_id
    rows = session.exec(
        select(Friendship)
        .where(col == me.id, Friendship.status == STATUS_PENDING)
        .order_by(Friendship.created_at.desc())
    ).all()
    return [to_read(r, session) for r in rows]


@router.post("/friend-requests/{req_id}/accept", response_model=FriendRequestRead)
def accept_request(
    req_id: int,
    background: BackgroundTasks,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    return respond(load_incoming(req_id, me, session), me, "accept", session, background)


@router.post("/friend-requests/{req_id}/decline", response_model=FriendRequestRead)
def decline_request(
    req_id: int,
    background: BackgroundTasks,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    return respond(load_incoming(req_id, me, session), me, "decline", session, background)


@router.delete("/friend-requests/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_request(
    req_id: int,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    row = session.get(Friendship, req_id)
    if row is None or row.sender_id != me.id or row.status != STATUS_PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")
    session.delete(row)
    session.commit()


@router.post("/friend-requests/lookup", response_model=FriendRequestRead)
def lookup_by_link(
    body: LookupBody,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    row = session.get(Friendship, parse_link_id(body.token))
    if row is None or me.id not in (row.sender_id, row.reciever_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This link is invalid")
    return to_read(row, session)


@router.post("/friend-requests/respond", response_model=FriendRequestRead)
def respond_by_link(
    body: RespondBody,
    background: BackgroundTasks,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    row = session.get(Friendship, parse_link_id(body.token))
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This request no longer exists")
    if row.reciever_id != me.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "This request was sent to a different account. Log in with that account to respond.")
    if row.status != STATUS_PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "You're already friends")
    return respond(row, me, body.action, session, background)


@router.get("/friends", response_model=list[FriendRead])
def list_friends(
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(Friendship).where(
            Friendship.status == STATUS_ACCEPTED,
            or_(Friendship.sender_id == me.id, Friendship.reciever_id == me.id),
        )
    ).all()
    out = []
    for f in rows:
        other = session.get(Profile, f.reciever_id if f.sender_id == me.id else f.sender_id)
        if other is not None:
            out.append(FriendRead(user=brief(other), level=f.level, since=f.created_at))
    out.sort(key=lambda f: f.user.display_name.lower())
    return out


@router.delete("/friends/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    profile_id: uuid.UUID,
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    row = row_between(me.id, profile_id, session)
    if row is None or row.status != STATUS_ACCEPTED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "You're not friends with that user")
    session.delete(row)
    session.commit()
