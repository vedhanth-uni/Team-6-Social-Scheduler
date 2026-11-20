# a friend's events for the friends checklist on the dashboard
#
#   GET /friends/{profile_id}/events?start=...&end=...
#
# you have to be friends (accepted). private events never show. close and professional
# friends both see public + professional for now, events don't have a "close" option yet.

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlmodel import Session, select

from app.auth_profile import current_profile
from app.database import get_session
from app.models.calendar import Calendar
from app.models.event import Event
from app.models.friendships import STATUS_ACCEPTED, Friendship
from app.models.profile import Profile
from app.services import recurrence

router = APIRouter(tags=["Friends"])

VISIBLE_TO = {
    "close": {"public", "professional"},
    "professional": {"public", "professional"},
}


class FriendOccurrence(BaseModel):
    event_id: int
    title: str
    location: str | None
    start: datetime
    end: datetime
    all_day: bool
    visibility: str


@router.get("/friends/{profile_id}/events", response_model=list[FriendOccurrence])
def friend_events(
    profile_id: uuid.UUID,
    start: datetime = Query(description="window start, iso (no offset = utc)"),
    end: datetime = Query(description="window end, iso (no offset = utc)"),
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    start = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    end = end if end.tzinfo else end.replace(tzinfo=timezone.utc)
    if end <= start:
        raise HTTPException(422, "end must be after start")

    friendship = session.exec(
        select(Friendship).where(
            Friendship.status == STATUS_ACCEPTED,
            or_(
                (Friendship.sender_id == me.id) & (Friendship.reciever_id == profile_id),
                (Friendship.sender_id == profile_id) & (Friendship.reciever_id == me.id),
            ),
        )
    ).first()
    if friendship is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "You're not friends with that user")

    allowed = VISIBLE_TO.get(friendship.level, {"public"})
    cal_ids = select(Calendar.id).where(Calendar.owner_id == profile_id, Calendar.deleted_at == None)  # noqa: E711
    events = session.exec(
        select(Event).where(
            Event.calendar_id.in_(cal_ids),
            Event.deleted_at == None,  # noqa: E711
            Event.visibility.in_(allowed),
        )
    ).all()

    out = []
    for ev in events:
        for s, e in recurrence.expand(ev.start_local, ev.end_local, ev.timezone, ev.rrule, start, end):
            out.append(FriendOccurrence(
                event_id=ev.id,
                title=ev.title,
                location=ev.location,
                start=s,
                end=e,
                all_day=ev.all_day,
                visibility=ev.visibility,
            ))
    out.sort(key=lambda o: o.start)
    return out
