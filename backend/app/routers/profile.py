# profiles are made automatically on first login (see auth_profile.py) and edited with PATCH /me,
# so the only thing left here is searching for other people to add as friends.

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, or_, select

from app.auth_profile import current_profile
from app.database import get_session
from app.models.profile import Profile
from app.schemas.profile import ProfilePublic

router = APIRouter(prefix="/profiles", tags=["profiles"])


def escape_like(text: str) -> str:
    """% and _ are wildcards in LIKE. Escape them so user input is taken literally.
    This matters because underscores are valid in usernames."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/search", response_model=list[ProfilePublic])
def search_profiles(
    q: str = Query(min_length=1, max_length=30),
    limit: int = Query(default=20, ge=1, le=50),
    me: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    pattern = f"%{escape_like(q.strip().lower())}%"
    statement = (
        select(Profile)
        .where(Profile.id != me.id)  # don't return the searcher
        .where(
            or_(
                col(Profile.username).ilike(pattern, escape="\\"),
                col(Profile.display_name).ilike(pattern, escape="\\"),
            )
        )
        .order_by(Profile.username)
        .limit(limit)
    )
    return session.exec(statement).all()