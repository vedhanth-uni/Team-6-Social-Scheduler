import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.auth_profile import current_profile, get_or_create_calendar
from app.database import get_session
from app.models.profile import Profile
from app.models.profile_email import ProfileEmail
from app.schemas.profile import ProfileUpdate

router = APIRouter(tags=["Me"])


class MeRead(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str
    email: str | None
    calendar_id: int


def build_me(profile: Profile, session: Session) -> MeRead:
    row = session.get(ProfileEmail, profile.id)
    cal = get_or_create_calendar(profile, session)  # also covers profiles made before calendars existed
    return MeRead(id=profile.id, username=profile.username, display_name=profile.display_name,
                  email=row.email if row else None, calendar_id=cal.id)


# the frontend calls this right after login, it also makes the profile on the first visit
@router.get("/me", response_model=MeRead)
def me(profile: Profile = Depends(current_profile), session: Session = Depends(get_session)):
    return build_me(profile, session)


# usernames start out as whatever comes before the @ in the email, this is how people pick their own
@router.patch("/me", response_model=MeRead)
def update_me(
    body: ProfileUpdate,
    profile: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    sent = body.model_dump(exclude_unset=True)
    for field in ("username", "display_name"):
        if sent.get(field) is not None:
            setattr(profile, field, sent[field])
    session.add(profile)
    try:
        session.commit()
    except IntegrityError:
        # the unique constraint on username is the real guard, even if two requests race
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    session.refresh(profile)
    return build_me(profile, session)