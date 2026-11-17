import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.auth_profile import current_profile
from app.database import get_session
from app.models.calendar import Calendar, CalendarShare
from app.models.profile import Profile
from app.models.timeutil import utcnow
from app.schemas.calendar import (
    CalendarCreate,
    CalendarRead,
    CalendarUpdate,
    ShareCreate,
    ShareRead,
)

router = APIRouter(prefix="/calendars", tags=["Calendars"])

Access = Literal["owner", "editor", "viewer"]
RANK = {"viewer": 1, "editor": 2, "owner": 3}


def access_level(cal: Calendar, user_id: uuid.UUID, session: Session) -> Access | None:
    if cal.owner_id == user_id:
        return "owner"
    share = session.get(CalendarShare, (cal.id, user_id))
    return share.permission if share else None


def load_calendar(cal_id: int, user: Profile, session: Session, need: Access) -> tuple[Calendar, Access]:
    cal = session.get(Calendar, cal_id)
    access = access_level(cal, user.id, session) if cal and cal.deleted_at is None else None
    if access is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calendar not found")
    if RANK[access] < RANK[need]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires {need} access")
    return cal, access


def to_read(cal: Calendar, access: Access) -> CalendarRead:
    return CalendarRead(**cal.model_dump(), my_access=access)


def share_to_read(share: CalendarShare, profile: Profile) -> ShareRead:
    return ShareRead(
        **share.model_dump(),
        username=profile.username,
        display_name=profile.display_name,
    )


@router.post("", response_model=CalendarRead, status_code=status.HTTP_201_CREATED)
def create_calendar(
    body: CalendarCreate,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    has_any = session.exec(
        select(Calendar.id).where(Calendar.owner_id == user.id, Calendar.deleted_at == None)  # noqa: E711
    ).first()
    cal = Calendar(**body.model_dump(), owner_id=user.id, is_primary=has_any is None)
    session.add(cal)
    session.commit()
    session.refresh(cal)
    return to_read(cal, "owner")


@router.get("", response_model=list[CalendarRead])
def list_my_calendars(
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    owned = session.exec(
        select(Calendar).where(Calendar.owner_id == user.id, Calendar.deleted_at == None)  # noqa: E711
    ).all()
    shared = session.exec(
        select(Calendar, CalendarShare.permission)
        .join(CalendarShare, CalendarShare.calendar_id == Calendar.id)
        .where(CalendarShare.user_id == user.id, Calendar.deleted_at == None)  # noqa: E711
    ).all()
    return [to_read(c, "owner") for c in owned] + [to_read(c, perm) for c, perm in shared]


@router.get("/{cal_id}", response_model=CalendarRead)
def get_calendar(
    cal_id: int,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    cal, access = load_calendar(cal_id, user, session, need="viewer")
    return to_read(cal, access)


@router.patch("/{cal_id}", response_model=CalendarRead)
def update_calendar(
    cal_id: int,
    body: CalendarUpdate,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    cal, access = load_calendar(cal_id, user, session, need="editor")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cal, field, value)
    cal.updated_at = utcnow()
    session.add(cal)
    session.commit()
    session.refresh(cal)
    return to_read(cal, access)


@router.delete("/{cal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar(
    cal_id: int,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    cal, _ = load_calendar(cal_id, user, session, need="owner")
    cal.deleted_at = utcnow()
    session.add(cal)
    session.commit()


@router.post("/{cal_id}/shares", response_model=ShareRead, status_code=status.HTTP_201_CREATED)
def share_calendar(
    cal_id: int,
    body: ShareCreate,
    response: Response,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    load_calendar(cal_id, user, session, need="owner")

    target = session.exec(
        select(Profile).where(Profile.username == body.username.strip().lower())
    ).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user with that username")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You already own this calendar")

    share = session.get(CalendarShare, (cal_id, target.id))
    if share:
        share.permission = body.permission
        share.relationship = body.relationship
        response.status_code = status.HTTP_200_OK
    else:
        share = CalendarShare(
            calendar_id=cal_id,
            user_id=target.id,
            permission=body.permission,
            relationship=body.relationship,
        )
    session.add(share)
    session.commit()
    session.refresh(share)
    return share_to_read(share, target)


@router.get("/{cal_id}/shares", response_model=list[ShareRead])
def list_shares(
    cal_id: int,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    load_calendar(cal_id, user, session, need="owner")
    rows = session.exec(
        select(CalendarShare, Profile)
        .join(Profile, Profile.id == CalendarShare.user_id)
        .where(CalendarShare.calendar_id == cal_id)
    ).all()
    return [share_to_read(s, p) for s, p in rows]


@router.delete("/{cal_id}/shares/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_share(
    cal_id: int,
    user_id: uuid.UUID,
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    need: Access = "viewer" if user_id == user.id else "owner"
    load_calendar(cal_id, user, session, need=need)
    share = session.get(CalendarShare, (cal_id, user_id))
    if share is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not shared with that user")
    session.delete(share)
    session.commit()
