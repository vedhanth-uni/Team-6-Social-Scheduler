# Runs for every test: point the backend at a fake Supabase project and make it trust our test key.

from types import SimpleNamespace

import pytest

from app import auth
from app.config import settings
from tests.auth_helpers import HS_SECRET, PUBLIC_KEY, SUPABASE_URL  # noqa: F401


class FakeJWKS:
    """Stands in for the client that downloads Supabase's public keys."""

    def get_signing_key_from_jwt(self, token):
        return SimpleNamespace(key=PUBLIC_KEY)


@pytest.fixture(autouse=True)
def supabase_auth(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", SUPABASE_URL)
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    monkeypatch.setattr(auth, "_jwks_client", lambda url: FakeJWKS())
