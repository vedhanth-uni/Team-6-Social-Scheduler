import re
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.supabase_auth import get_current_claims, get_current_user_id
from app.database import get_session
from app.models.calendar import Calendar
from app.models.profile import Profile
from app.models.profile_email import ProfileEmail


def pick_username(email: str, session: Session) -> str:
    base = re.sub(r"[^a-z0-9_]", "", email.split("@")[0].lower())[:24]
    if len(base) < 3:
        base = (base + "user")[:24]
    name, n = base, 1
    while session.exec(select(Profile).where(Profile.username == name)).first():
        n += 1
        name = f"{base}{n}"
    return name


def get_or_create_calendar(profile: Profile, session: Session) -> Calendar:
    # every user has exactly one calendar (calendars.owner_id is unique)
    cal = session.exec(select(Calendar).where(Calendar.owner_id == profile.id)).first()
    if cal is not None:
        if cal.deleted_at is not None:
            cal.deleted_at = None
            session.add(cal)
            session.commit()
            session.refresh(cal)
        return cal

    cal = Calendar(owner_id=profile.id, name=f"{profile.display_name}'s calendar", is_primary=True)
    session.add(cal)
    try:
        session.commit()
    except IntegrityError:
        # the dashboard fires a few requests at once and another one made it first
        session.rollback()
        cal = session.exec(select(Calendar).where(Calendar.owner_id == profile.id)).first()
        if cal is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Could not create your calendar")
        return cal
    session.refresh(cal)
    return cal


def make_profile(user_id: uuid.UUID, claims: dict, session: Session) -> Profile:
    # first visit after logging in, so make their profile from the login info
    email = (claims.get("email") or "").strip().lower()
    meta = claims.get("user_metadata") or {}
    display = (meta.get("full_name") or meta.get("name") or email.split("@")[0] or "New user").strip()[:50]
    profile = Profile(id=user_id, username=pick_username(email or "user", session), display_name=display)
    session.add(profile)
    try:
        session.commit()
    except IntegrityError:
        # the dashboard fires a few requests at once and another one made it first
        session.rollback()
        profile = session.get(Profile, user_id)
        if profile is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Could not create your profile")
    session.refresh(profile)
    get_or_create_calendar(profile, session)#if u make a profile ur gonna get a calendar automatically
    return profile


def save_email(user_id: uuid.UUID, claims: dict, session: Session) -> None:
    email = (claims.get("email") or "").strip().lower()
    if not email:
        return
    row = session.get(ProfileEmail, user_id)
    if row and row.email == email:
        return
    if row:
        row.email = email
    else:
        row = ProfileEmail(profile_id=user_id, email=email)
    session.add(row)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def current_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    claims: dict = Depends(get_current_claims),
    session: Session = Depends(get_session),
) -> Profile:
    profile = session.get(Profile, user_id)
    if profile is None:
        profile = make_profile(user_id, claims, session)
    save_email(user_id, claims, session)
    return profile


def get_current_cal_id(
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
) -> int:
    # the id of the logged in user's own calendar, taken from their token, never from the client.
    # endpoints that depend on this don't take a calendar id at all, so nobody can aim one at
    # somebody else's calendar.
    return get_or_create_calendar(me, session).id