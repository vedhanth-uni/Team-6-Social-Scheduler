import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.auth_profile import current_profile
from app.database import get_session
from app.models.profile import Profile
from app.models.profile_email import ProfileEmail

router = APIRouter(tags=["Me"])


class MeRead(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str
    email: str | None


# the frontend calls this right after login, it also makes the profile on the first visit
@router.get("/me", response_model=MeRead)
def me(profile: Profile = Depends(current_profile), session: Session = Depends(get_session)):
    row = session.get(ProfileEmail, profile.id)
    return MeRead(id=profile.id, username=profile.username, display_name=profile.display_name,
                  email=row.email if row else None)
