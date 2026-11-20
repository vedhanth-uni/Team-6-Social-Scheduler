import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

# app.database refuses to import without DATABASE_URL, so point it at a throwaway sqlite file.
# conftest loads before any test module, and the app imports below happen inside fixtures,
# so nothing from app is imported before this line runs.
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()) / 'test.db'}"


class AuthAs:
    """Swaps the logged-in user for a test, instead of verifying a real Supabase token."""

    def __init__(self) -> None:
        self.profile_id: uuid.UUID | None = None

    def __call__(self, profile) -> None:
        self.profile_id = profile.id

    def claims(self) -> dict:
        assert self.profile_id is not None, "call auth_as(profile) before making a request"
        return {"sub": str(self.profile_id)}


@pytest.fixture
def session():
    from app.database import engine
    from app.main import app  # noqa: F401 (registers every table on SQLModel.metadata)

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


@pytest.fixture
def auth_as():
    from app.main import app
    from app.supabase_auth import get_current_claims

    auth = AuthAs()
    app.dependency_overrides[get_current_claims] = auth.claims
    yield auth
    app.dependency_overrides.clear()


@pytest.fixture
def client(session, auth_as):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_profile(session):
    from app.models.profile import Profile

    def make(username: str) -> Profile:
        profile = Profile(id=uuid.uuid4(), username=username, display_name=username.title())
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile

    return make
