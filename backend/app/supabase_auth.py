# checks the supabase login token on every request
#
# the frontend sends "Authorization: Bearer <access_token>". supabase signs it with a key
# published at {SUPABASE_URL}/auth/v1/.well-known/jwks.json, so we check it with the public key.
# older projects sign with a shared secret instead, that only works if SUPABASE_JWT_SECRET is set.

import logging
import uuid
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError

from app.config import settings

log = logging.getLogger(__name__)

ASYMMETRIC_ALGS = ("ES256", "RS256")
SYMMETRIC_ALGS = ("HS256",)
CLOCK_SKEW_SECONDS = 10

bearer_scheme = HTTPBearer(auto_error=False, description="Supabase access token")


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_jwk_set=True, lifespan=600, timeout=5)


def _signing_key(token: str, alg: str):
    if alg in SYMMETRIC_ALGS:
        if not settings.SUPABASE_JWT_SECRET:
            raise unauthorized("Invalid token")
        return settings.SUPABASE_JWT_SECRET
    return _jwks_client(f"{settings.issuer}/.well-known/jwks.json").get_signing_key_from_jwt(token).key


def verify_token(token: str) -> dict:
    if not settings.SUPABASE_URL:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SUPABASE_URL is not set on the server")
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
        log.exception("could not fetch supabase signing keys")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Authentication service unavailable")
    except jwt.PyJWTError:
        raise unauthorized("Invalid token")


def get_current_claims(creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if creds is None:
        raise unauthorized("Not authenticated")
    return verify_token(creds.credentials)


def get_current_user_id(claims: dict = Depends(get_current_claims)) -> uuid.UUID:
    # profile ids are the supabase user id, so the token's sub is all we need
    try:
        return uuid.UUID(claims["sub"])
    except ValueError:
        raise unauthorized("Invalid token")
