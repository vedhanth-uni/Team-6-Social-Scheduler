import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, and_, col, or_, select

from app.auth import get_current_user_id
from app.database import get_session
from app.mocks import fetch_user_events, send_friend_request_email
from app.models.friendships import (
    LEVEL_CLOSE,
    STATUS_ACCEPTED,
    STATUS_PENDING,
    Friendship,
)
from app.models.profile import Profile
from app.schemas.event import EventOut
from app.schemas.friends import (
    FriendLevelUpdate,
    FriendOut,
    FriendRequestCreate,
    FriendRequestOut,
    FriendsOverview,
)
from app.schemas.profile import ProfilePublic

router = APIRouter(prefix="/friends", tags=["friends"])


# ---------- helpers ----------

def get_row_between(session: Session, a: uuid.UUID, b: uuid.UUID) -> Friendship | None:
    """The row linking two users, whichever of them is sender or receiver."""
    return session.exec(
        select(Friendship).where(
            or_(
                and_(Friendship.sender_id == a, Friendship.receiver_id == b),
                and_(Friendship.sender_id == b, Friendship.receiver_id == a),
            )
        )
    ).first()


def get_accepted_friendship(session: Session, me: uuid.UUID, friend_id: uuid.UUID) -> Friendship:
    row = get_row_between(session, me, friend_id)
    if row is None or row.status != STATUS_ACCEPTED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not friends with this user")
    return row


def other_id(row: Friendship, me: uuid.UUID) -> uuid.UUID:
    return row.receiver_id if row.sender_id == me else row.sender_id


def load_profiles(session: Session, ids: set[uuid.UUID]) -> dict[uuid.UUID, Profile]:
    if not ids:
        return {}
    profiles = session.exec(select(Profile).where(col(Profile.id).in_(list(ids)))).all()
    return {p.id: p for p in profiles}


def hide_private_details(events: list[EventOut]) -> list[EventOut]:
    """Regular friends see private events as anonymous 'busy' blocks."""
    return [
        e.model_copy(update={"title": None, "details_hidden": True}) if e.is_private else e
        for e in events
    ]


# ---------- 1. overview: friends + count + pending requests ----------

@router.get("", response_model=FriendsOverview)
def get_friends_overview(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    rows = session.exec(
        select(Friendship)
        .where(or_(Friendship.sender_id == user_id, Friendship.receiver_id == user_id))
        .order_by(col(Friendship.created_at).desc())
    ).all()

    profiles = load_profiles(session, {other_id(r, user_id) for r in rows})

    friends: list[FriendOut] = []
    incoming: list[FriendRequestOut] = []
    outgoing: list[FriendRequestOut] = []

    for row in rows:
        other = profiles.get(other_id(row, user_id))
        if other is None:  # shouldn't happen thanks to the foreign keys
            continue
        public = ProfilePublic.model_validate(other)
        if row.status == STATUS_ACCEPTED:
            friends.append(FriendOut(friend=public, level=row.level))
        else:
            item = FriendRequestOut(
                id=row.id, user=public, status=row.status, created_at=row.created_at
            )
            (incoming if row.receiver_id == user_id else outgoing).append(item)

    friends.sort(key=lambda f: f.friend.username)
    return FriendsOverview(
        friend_count=len(friends),
        friends=friends,
        incoming_requests=incoming,
        outgoing_requests=outgoing,
    )


# ---------- send request (not on your list, but needed to test the rest) ----------

@router.post("/requests", response_model=FriendRequestOut, status_code=status.HTTP_201_CREATED)
def send_friend_request(
    data: FriendRequestCreate,
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if data.receiver_id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't send a request to yourself")

    sender = session.get(Profile, user_id)
    if sender is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Create your profile first")

    receiver = session.get(Profile, data.receiver_id)
    if receiver is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    existing = get_row_between(session, user_id, data.receiver_id)
    if existing is not None:
        if existing.status == STATUS_ACCEPTED:
            raise HTTPException(status.HTTP_409_CONFLICT, "Already friends")
        if existing.sender_id == user_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Request already sent")
        # They already asked me, so sending one back means "yes": accept theirs.
        existing.status = STATUS_ACCEPTED
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return FriendRequestOut(
            id=existing.id,
            user=ProfilePublic.model_validate(receiver),
            status=existing.status,
            created_at=existing.created_at,
        )

    row = Friendship(sender_id=user_id, receiver_id=data.receiver_id)
    session.add(row)
    try:
        session.commit()
    except IntegrityError:  # two simultaneous sends hit the unique constraint
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Request already exists")
    session.refresh(row)

    # Runs after the response is sent, so email problems never fail the request.
    background_tasks.add_task(
        send_friend_request_email,
        receiver_id=data.receiver_id,
        sender_username=sender.username,
    )
    return FriendRequestOut(
        id=row.id,
        user=ProfilePublic.model_validate(receiver),
        status=row.status,
        created_at=row.created_at,
    )


# ---------- 5. accept ----------

@router.post("/requests/{request_id}/accept", response_model=FriendOut)
def accept_friend_request(
    request_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    row = session.get(Friendship, request_id)
    # 404 (not 403) when it isn't yours, so we don't reveal that the row exists.
    if row is None or row.receiver_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    if row.status != STATUS_PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Request was already accepted")

    row.status = STATUS_ACCEPTED
    session.add(row)
    session.commit()
    session.refresh(row)

    sender = session.get(Profile, row.sender_id)
    return FriendOut(friend=ProfilePublic.model_validate(sender), level=row.level)


# ---------- 3. reject (receiver) or cancel (sender) ----------

@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def reject_or_cancel_request(
    request_id: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    row = session.get(Friendship, request_id)
    if row is None or user_id not in (row.sender_id, row.receiver_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    if row.status != STATUS_PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already friends. Remove the friend instead")

    session.delete(row)
    session.commit()


# ---------- 2. remove friend ----------

@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    row = get_accepted_friendship(session, user_id, friend_id)
    session.delete(row)
    session.commit()


# ---------- 6. update relationship ----------

@router.patch("/{friend_id}/level", response_model=FriendOut)
def update_friend_level(
    friend_id: uuid.UUID,
    data: FriendLevelUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    # TODO: levels are mutual, and "close" exposes private events in BOTH directions.
    # Once the team decides on consent, make this a request the other person must confirm.
    row = get_accepted_friendship(session, user_id, friend_id)
    row.level = data.level
    session.add(row)
    session.commit()
    session.refresh(row)

    friend = session.get(Profile, friend_id)
    return FriendOut(friend=ProfilePublic.model_validate(friend), level=row.level)


# ---------- 4. friend's events ----------

@router.get("/{friend_id}/events", response_model=list[EventOut])
def get_friend_events(
    friend_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    row = get_accepted_friendship(session, user_id, friend_id)
    events = fetch_user_events(friend_id)  # MOCK until the events feature exists
    if row.level == LEVEL_CLOSE:
        return events
    return hide_private_details(events)