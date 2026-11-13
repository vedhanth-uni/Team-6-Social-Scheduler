# Supabase authentication for the API.
#
# The frontend logs people in with Supabase and sends the access token (a JWT) on every request:
#     Authorization: Bearer <access_token>
# Everything below runs on the backend and never trusts the frontend:
#   1. verify_token()  checks the signature, expiry, audience and issuer of the JWT
#   2. current_user()  turns a valid token into a row in our own `users` table
#
# Supabase signs tokens with an asymmetric key (ES256/RS256) published at
#   {SUPABASE_URL}/auth/v1/.well-known/jwks.json
# so we verify them locally with the public key -- no network call per request, and no
# secret on our side. Older projects still sign with a shared secret (HS256); that only
# works if SUPABASE_JWT_SECRET is set.
#
# Worth knowing: a token stays valid until it expires (1 hour by default) even if the person
# signs out in the meantime. That is normal for JWTs. The frontend refreshes tokens
# automatically, so keeping the expiry short in the Supabase dashboard limits this window.

import logging
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models.user import User

log = logging.getLogger(__name__)

# the only algorithms we accept. Never "none", and HS256 only when a secret is configured --
# so a token can't pick an algorithm that makes our public key act as an HMAC secret.
ASYMMETRIC_ALGS = ("ES256", "RS256")
SYMMETRIC_ALGS = ("HS256",)
CLOCK_SKEW_SECONDS = 10

# auto_error=False so we can answer a missing header with our own 401 (and WWW-Authenticate)
bearer_scheme = HTTPBearer(auto_error=False, description="Supabase access token")


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    # caches the key set (and refetches when it sees an unknown key id, e.g. after a rotation)
    return PyJWKClient(url, cache_jwk_set=True, lifespan=600, timeout=5)


def _signing_key(token: str, alg: str):
    """The key to check this token's signature with."""
    if alg in SYMMETRIC_ALGS:
        if not settings.SUPABASE_JWT_SECRET:
            raise unauthorized("Invalid token")
        return settings.SUPABASE_JWT_SECRET
    return _jwks_client(f"{settings.issuer}/.well-known/jwks.json").get_signing_key_from_jwt(token).key


def verify_token(token: str) -> dict:
    """Return the token's claims if it is genuine, unexpired and meant for this app. Otherwise 401."""
    try:
        alg = jwt.get_unverified_header(token).get("alg")
        if alg not in ASYMMETRIC_ALGS + SYMMETRIC_ALGS:
            raise unauthorized("Invalid token")
        return jwt.decode(
            token,
            _signing_key(token, alg),
            algorithms=[alg],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=settings.issuer,
            leeway=CLOCK_SKEW_SECONDS,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise unauthorized("Token expired")
    except PyJWKClientConnectionError:
        # Supabase unreachable: that's our problem, not the user's -- don't make the frontend log them out
        log.exception("could not fetch Supabase signing keys")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication service unavailable")
    except jwt.PyJWTError:
        raise unauthorized("Invalid token")


def _display_name(claims: dict, email: str) -> str:
    meta = claims.get("user_metadata") or {}
    return (meta.get("full_name") or meta.get("name") or email.split("@")[0]).strip()


def _provision(claims: dict, session: Session) -> User:
    """First request from a Supabase user: create (or link) their row in our users table."""
    sub = claims["sub"]
    email = (claims.get("email") or "").strip().lower()
    if not email:
        # e.g. Supabase anonymous sign-ins. Our users need an email (friend requests, sharing)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your account has no email address")

    user = session.exec(select(User).where(func.lower(User.email) == email)).first()
    if user is not None:
        if user.auth_id not in (None, sub):
            raise HTTPException(status.HTTP_409_CONFLICT, "That email belongs to a different account")
        # A row already exists for this email (created before auth existed). Only attach the login
        # to it if the email is verified, otherwise anyone could sign up as someone else's address.
        if not (claims.get("user_metadata") or {}).get("email_verified"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Verify your email address to continue")
        user.auth_id = sub
    else:
        user = User(auth_id=sub, email=email, display_name=_display_name(claims, email))

    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # the dashboard fires several requests at once; another one created the row first
        session.rollback()
        user = session.exec(select(User).where(User.auth_id == sub)).first()
        if user is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Could not create your account")
        return user
    session.refresh(user)
    return user


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Dependency for every protected route: a valid Supabase token -> the matching User."""
    if creds is None:
        raise unauthorized("Not authenticated")
    claims = verify_token(creds.credentials)

    user = session.exec(select(User).where(User.auth_id == claims["sub"])).first()
    if user is None:
        user = _provision(claims, session)
    if user.deleted_at is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deleted")
    return user
