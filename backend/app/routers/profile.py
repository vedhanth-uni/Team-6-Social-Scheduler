import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, or_, select

from app.auth import get_current_user_id
from app.database import get_session
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfilePublic

router = APIRouter(prefix="/profiles", tags=["profiles"])


def escape_like(text: str) -> str:
    """% and _ are wildcards in LIKE. Escape them so user input is taken literally.
    This matters because underscores are valid in usernames."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.post("", response_model=ProfilePublic, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if session.get(Profile, user_id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Profile already exists for this user")

    profile = Profile(id=user_id, username=data.username, display_name=data.display_name)
    session.add(profile)
    try:
        session.commit()
    except IntegrityError:
        # The database's unique constraint is the real guard against duplicate
        # usernames, even if two requests race each other.
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    session.refresh(profile)
    return profile


@router.get("/me", response_model=ProfilePublic)
def get_my_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    profile = session.get(Profile, user_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    return profile


@router.get("/search", response_model=list[ProfilePublic])
def search_profiles(
    q: str = Query(min_length=1, max_length=30),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    pattern = f"%{escape_like(q.strip().lower())}%"
    statement = (
        select(Profile)
        .where(Profile.id != user_id)  # don't return the searcher
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