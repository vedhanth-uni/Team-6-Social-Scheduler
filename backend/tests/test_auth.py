# Run from the backend/ folder:  python -m pytest tests/test_auth.py
# These tests use real signed tokens (see auth_helpers.py), so the actual verification code runs.

import base64
import hashlib
import hmac
import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError
from sqlmodel import select

from app import auth
from app.auth import current_user
from app.config import settings
from app.main import app
from app.models.user import User
from tests.auth_helpers import HS_SECRET, ISSUER, PUBLIC_KEY, auth_headers, bearer, make_token
from tests.test_calendars import client, session, users  # noqa: F401

# routes that are meant to work without logging in
PUBLIC_PATHS = {"/", "/health", "/health/db", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def get_me(client, token):
    return client.get("/me", headers=bearer(token))


# ---------- every route is protected unless it is on the public list ----------

def depends_on_current_user(dependant) -> bool:
    return any(d.call is current_user or depends_on_current_user(d) for d in dependant.dependencies)


def test_every_route_requires_login_unless_public():
    unprotected = [
        r.path for r in app.routes
        if hasattr(r, "dependant") and r.path not in PUBLIC_PATHS and not depends_on_current_user(r.dependant)
    ]
    assert unprotected == [], f"these routes don't require login: {unprotected}"


def test_old_dev_header_no_longer_works(client, users):
    alice, *_ = users
    assert client.get("/calendars", headers={"X-User-Id": str(alice.id)}).status_code == 401


# ---------- token checks ----------

def test_no_token(client):
    r = client.get("/me")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_valid_token(client, users):
    alice, *_ = users
    r = client.get("/me", headers=auth_headers(alice))
    assert r.status_code == 200
    assert r.json() == {"id": alice.id, "email": "alice@umass.edu", "display_name": "Alice"}


def test_garbage_token(client):
    assert get_me(client, "not-a-jwt").status_code == 401


def test_expired_token(client, users):
    alice, *_ = users
    r = get_me(client, make_token(alice.auth_id, alice.email, exp_in=-60))
    assert r.status_code == 401
    assert r.json()["detail"] == "Token expired"


def test_small_clock_skew_is_tolerated(client, users):
    alice, *_ = users
    assert get_me(client, make_token(alice.auth_id, alice.email, exp_in=-3)).status_code == 200


def test_wrong_audience(client, users):
    alice, *_ = users
    assert get_me(client, make_token(alice.auth_id, alice.email, aud="something-else")).status_code == 401


def test_wrong_issuer(client, users):
    alice, *_ = users
    token = make_token(alice.auth_id, alice.email, iss="https://evil.supabase.co/auth/v1")
    assert get_me(client, token).status_code == 401


def test_signed_with_someone_elses_key(client, users):
    alice, *_ = users
    forged = make_token(alice.auth_id, alice.email, key=ec.generate_private_key(ec.SECP256R1()))
    assert get_me(client, forged).status_code == 401


@pytest.mark.parametrize("claim", ["sub", "exp", "aud", "iss"])
def test_required_claims(client, users, claim):
    alice, *_ = users
    assert get_me(client, make_token(alice.auth_id, alice.email, drop=(claim,))).status_code == 401


def test_unsigned_token_rejected(client, users):
    alice, *_ = users
    unsigned = jwt.encode({"sub": alice.auth_id, "aud": "authenticated", "iss": ISSUER, "exp": 9999999999},
                          key=None, algorithm="none")
    assert get_me(client, unsigned).status_code == 401


def test_hs256_rejected_when_no_secret_configured(client, users):
    alice, *_ = users
    assert get_me(client, make_token(alice.auth_id, alice.email, key=HS_SECRET, alg="HS256")).status_code == 401


def test_hs256_public_key_confusion_rejected(client, users):
    # classic attack: sign with HS256 using the *public* key as the secret. PyJWT refuses to build
    # such a token, so assemble it by hand the way an attacker would.
    alice, *_ = users
    public_pem = PUBLIC_KEY.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    def b64(raw: bytes) -> bytes:
        return base64.urlsafe_b64encode(raw).rstrip(b"=")

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64(json.dumps({"sub": alice.auth_id, "aud": "authenticated", "iss": ISSUER, "exp": 9999999999}).encode())
    signature = b64(hmac.new(public_pem, header + b"." + payload, hashlib.sha256).digest())
    forged = (header + b"." + payload + b"." + signature).decode()

    assert get_me(client, forged).status_code == 401


def test_hs256_accepted_for_legacy_projects(client, users, monkeypatch):
    alice, *_ = users
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", HS_SECRET)
    assert get_me(client, make_token(alice.auth_id, alice.email, key=HS_SECRET, alg="HS256")).status_code == 200


def test_legacy_secret_does_not_accept_wrong_secret(client, users, monkeypatch):
    alice, *_ = users
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", HS_SECRET)
    bad = make_token(alice.auth_id, alice.email, key=HS_SECRET + "x", alg="HS256")
    assert get_me(client, bad).status_code == 401


def test_unknown_key_id_is_401(client, users, monkeypatch):
    alice, *_ = users

    class NoSuchKey:
        def get_signing_key_from_jwt(self, token):
            raise PyJWKClientError("Unable to find a signing key that matches")

    monkeypatch.setattr(auth, "_jwks_client", lambda url: NoSuchKey())
    assert get_me(client, make_token(alice.auth_id, alice.email)).status_code == 401


def test_supabase_unreachable_is_503_not_401(client, users, monkeypatch):
    # a Supabase outage must not look like "your login is bad" or the frontend would sign everyone out
    alice, *_ = users

    class Down:
        def get_signing_key_from_jwt(self, token):
            raise PyJWKClientConnectionError("connection refused")

    monkeypatch.setattr(auth, "_jwks_client", lambda url: Down())
    assert get_me(client, make_token(alice.auth_id, alice.email)).status_code == 503


# ---------- tying a login to a row in `users` ----------

def test_first_login_creates_user(client, session):
    token = make_token("uuid-1", "New.Person@UMass.edu", user_metadata={"full_name": "New Person", "email_verified": True})
    r = get_me(client, token)
    assert r.status_code == 200
    assert r.json()["email"] == "new.person@umass.edu"
    assert r.json()["display_name"] == "New Person"

    user = session.exec(select(User).where(User.auth_id == "uuid-1")).one()
    assert user.id == r.json()["id"]


def test_display_name_falls_back_to_email_name(client):
    r = get_me(client, make_token("uuid-2", "sam@umass.edu", user_metadata={}))
    assert r.json()["display_name"] == "sam"


def test_second_login_reuses_the_same_user(client, session):
    first = get_me(client, make_token("uuid-3", "sam@umass.edu")).json()
    second = get_me(client, make_token("uuid-3", "sam@umass.edu")).json()
    assert first["id"] == second["id"]
    assert len(session.exec(select(User)).all()) == 1


def test_existing_row_is_linked_when_email_is_verified(client, session):
    old = User(email="legacy@umass.edu", display_name="Legacy")
    session.add(old)
    session.commit()
    r = get_me(client, make_token("uuid-4", "legacy@umass.edu"))
    assert r.status_code == 200
    assert r.json()["id"] == old.id
    session.refresh(old)
    assert old.auth_id == "uuid-4"


def test_existing_row_is_not_linked_when_email_unverified(client, session):
    # otherwise anyone could register someone else's address and inherit their calendars
    session.add(User(email="victim@umass.edu", display_name="Victim"))
    session.commit()
    r = get_me(client, make_token("uuid-5", "victim@umass.edu", user_metadata={"email_verified": False}))
    assert r.status_code == 403
    assert session.exec(select(User).where(User.auth_id == "uuid-5")).first() is None


def test_email_already_linked_to_another_login(client, users):
    alice, *_ = users
    r = get_me(client, make_token("a-different-uuid", alice.email))
    assert r.status_code == 409


def test_account_without_email_rejected(client):
    assert get_me(client, make_token("uuid-6", None, drop=("email",))).status_code == 403


def test_deleted_user_rejected(client, session, users):
    from app.models.timeutil import utcnow
    alice, *_ = users
    alice.deleted_at = utcnow()
    session.add(alice)
    session.commit()
    assert client.get("/me", headers=auth_headers(alice)).status_code == 403


def test_simultaneous_first_requests_do_not_create_duplicates(session):
    # two requests race: the second one's insert hits the unique auth_id and must fall back to the first row
    session.add(User(auth_id="uuid-7", email="other@umass.edu", display_name="Other"))
    session.commit()
    claims = {"sub": "uuid-7", "email": "racer@umass.edu", "user_metadata": {}}
    user = auth._provision(claims, session)
    assert user.email == "other@umass.edu"
    assert len(session.exec(select(User)).all()) == 1


# ---------- CORS ----------

def test_cors_allows_the_frontend_origin(client):
    origin = settings.CORS_ORIGINS[0]
    r = client.options("/calendars", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == origin


def test_cors_blocks_other_origins(client):
    r = client.options("/calendars", headers={
        "Origin": "https://evil.example",
        "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" not in r.headers


def test_cors_headers_present_on_401(client):
    origin = settings.CORS_ORIGINS[0]
    r = client.get("/calendars", headers={"Origin": origin})
    assert r.status_code == 401
    assert r.headers["access-control-allow-origin"] == origin
