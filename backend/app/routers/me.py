# GET /me -- who the api thinks you are. The frontend calls this right after login: it proves the
# token is accepted by the backend and creates the user's row on their very first visit.

from fastapi import APIRouter, Depends

from app.auth import current_user
from app.models.user import User
from app.schemas.friend import UserBrief

router = APIRouter(tags=["Me"])


@router.get("/me", response_model=UserBrief)
def me(user: User = Depends(current_user)):
    return UserBrief(id=user.id, email=user.email, display_name=user.display_name)
