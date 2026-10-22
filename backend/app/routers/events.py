# event routes
# owner and editors can edit. public events anyone can see, professional is only people
# the calendar is shared with, private is just owner and editors

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.calendar import Calendar, CalendarShare
from app.models.event import Attendee, Event
from app.models.timeutil import utcnow
from app.models.user import User
from app.routers.calendars import current_user
from app.schemas.event import EventCreate, EventRead, EventUpdate, Occurrence
from app.services import recurrence

router = APIRouter(tags=["Events"])

Access = Literal["edit", "view"]


def event_access(ev: Event, cal: Calendar, user: User, session: Session) -> Access | None:
    if ev.deleted_at is not None or cal.deleted_at is not None:
        return None
    if cal.owner_id == user.id:
        return "edit"
    share = session.get(CalendarShare, (cal.id, user.id))
    if share and share.permission == "editor":
        return "edit"
    if ev.visibility == "public":
        return "view"
    if share and ev.visibility == "professional":
        return "view"
    return None


def load_event(event_id: int, user: User, session: Session, need: Access) -> tuple[Event, Access]:
    ev = session.get(Event, event_id)
    cal = session.get(Calendar, ev.calendar_id) if ev else None
    access = event_access(ev, cal, user, session) if cal else None
    if access is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    if need == "edit" and access != "edit":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requires editor access")
    return ev, access


def bad(msg: str):
    raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)


def resolve_times(tz: str, all_day: bool, start: datetime, end: datetime | None) -> tuple[datetime, datetime]:
    try:
        start = recurrence.to_local(start, tz)
        end = recurrence.to_local(end, tz) if end else None
    except ValueError as e:
        bad(str(e))

    if all_day:
        # all day just means midnight to midnight
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        if end is None or end.date() <= start.date():
            end = start + timedelta(days=1)
        else:
            end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    elif end is None:
        bad("end is required unless all_day is true")
    elif end <= start:
        bad("end must be after start")
    return start, end


def validate_rrule(rule: str | None) -> str | None:
    if rule is None:
        return None
    try:
        return recurrence.check_rrule(rule)
    except ValueError as e:
        bad(str(e))


def has_joined(event_id: int, user: User, session: Session) -> bool:
    return session.exec(
        select(Attendee).where(Attendee.event_id == event_id, Attendee.user_id == user.id)
    ).first() is not None


def to_read(ev: Event, access: Access, joined: bool) -> EventRead:
    return EventRead(
        **ev.model_dump(exclude={"start_local", "end_local"}),
        start=recurrence.localize(ev.start_local, ev.timezone),
        end=recurrence.localize(ev.end_local, ev.timezone),
        can_edit=access == "edit",
        joined=joined,
    )


@router.post("/calendars/{cal_id}/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    cal_id: int,
    body: EventCreate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    cal = session.get(Calendar, cal_id)
    if cal is None or cal.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calendar not found")
    if cal.owner_id != user.id:
        share = session.get(CalendarShare, (cal.id, user.id))
        if share is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Calendar not found")
        if share.permission != "editor":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Requires editor access")

    tz = body.timezone or cal.timezone
    start, end = resolve_times(tz, body.all_day, body.start, body.end)
    ev = Event(
        **body.model_dump(exclude={"start", "end", "timezone", "rrule"}),
        calendar_id=cal.id,
        created_by=user.id,
        start_local=start,
        end_local=end,
        timezone=tz,
        rrule=validate_rrule(body.rrule),
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return to_read(ev, "edit", False)


@router.get("/calendars/{cal_id}/events", response_model=list[Occurrence])
def list_events(
    cal_id: int,
    start: datetime = Query(description="window start, iso (no offset = utc)"),
    end: datetime = Query(description="window end, iso (no offset = utc)"),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    start = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    end = end if end.tzinfo else end.replace(tzinfo=timezone.utc)
    if end <= start:
        bad("end must be after start")

    cal = session.get(Calendar, cal_id)
    if cal is None or cal.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calendar not found")

    events = session.exec(
        select(Event).where(Event.calendar_id == cal.id, Event.deleted_at == None)  # noqa: E711
    ).all()
    visible = [ev for ev in events if event_access(ev, cal, user, session)]

    has_cal_access = cal.owner_id == user.id or session.get(CalendarShare, (cal.id, user.id))
    if not has_cal_access and not visible:
        # not shared and nothing public so just 404
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calendar not found")

    out = []
    for ev in visible:
        joined = has_joined(ev.id, user, session)
        for s, e in recurrence.expand(ev.start_local, ev.end_local, ev.timezone, ev.rrule, start, end):
            out.append(Occurrence(
                event_id=ev.id,
                title=ev.title,
                start=s,
                end=e,
                all_day=ev.all_day,
                is_recurring=ev.rrule is not None,
                visibility=ev.visibility,
                joined=joined,
            ))
    out.sort(key=lambda o: o.start)
    return out


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    ev, access = load_event(event_id, user, session, need="view")
    return to_read(ev, access, has_joined(ev.id, user, session))


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    body: EventUpdate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    ev, access = load_event(event_id, user, session, need="edit")
    sent = body.model_dump(exclude_unset=True)

    for field in ("title", "description", "location", "visibility"):
        if field in sent:
            setattr(ev, field, sent[field])

    tz = sent.get("timezone") or ev.timezone
    all_day = sent["all_day"] if sent.get("all_day") is not None else ev.all_day
    start = sent.get("start") or ev.start_local
    if sent.get("end"):
        end = sent["end"]
    elif sent.get("start"):
        # keep the same length if they only moved the start
        end = recurrence.to_local(start, tz) + (ev.end_local - ev.start_local)
    else:
        end = ev.end_local
    ev.start_local, ev.end_local = resolve_times(tz, all_day, start, end)
    ev.timezone, ev.all_day = tz, all_day

    if "rrule" in sent:
        ev.rrule = validate_rrule(sent["rrule"])

    ev.updated_at = utcnow()
    session.add(ev)
    session.commit()
    session.refresh(ev)
    return to_read(ev, access, has_joined(ev.id, user, session))


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    ev, _ = load_event(event_id, user, session, need="edit")
    ev.deleted_at = utcnow()
    session.add(ev)
    session.commit()


@router.post("/events/{event_id}/join", status_code=status.HTTP_201_CREATED)
def join_event(
    event_id: int,
    response: Response,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    # if you can see it you can join it
    ev, _ = load_event(event_id, user, session, need="view")
    if has_joined(ev.id, user, session):
        response.status_code = status.HTTP_200_OK  # already joined
    else:
        session.add(Attendee(event_id=ev.id, user_id=user.id, email=user.email))
        session.commit()
    return {"event_id": ev.id, "joined": True}


@router.delete("/events/{event_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def leave_event(
    event_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    ev, _ = load_event(event_id, user, session, need="view")
    row = session.exec(
        select(Attendee).where(Attendee.event_id == ev.id, Attendee.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "You haven't joined this event")
    session.delete(row)
    session.commit()
