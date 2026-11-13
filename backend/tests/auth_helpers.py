# Helpers for minting fake Supabase access tokens in tests. Tokens are signed with a throwaway key
# that conftest.py swaps in for Supabase's real public key, so the real verification code runs.

import time

import jwt
from cryptography.hazmat.primitives.asymmetric import ec

SUPABASE_URL = "https://test-project.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"
HS_SECRET = "legacy-shared-secret-for-tests-0123456789"

PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
PUBLIC_KEY = PRIVATE_KEY.public_key()


def make_token(sub, email, *, exp_in=3600, key=None, alg="ES256", drop=(), **overrides):
    """A token shaped like the ones Supabase issues. `drop` removes claims, `overrides` replaces them."""
    now = int(time.time())
    claims = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "iss": ISSUER,
        "role": "authenticated",
        "iat": now,
        "exp": now + exp_in,
        "user_metadata": {"email_verified": True},
    }
    claims.update(overrides)
    for name in drop:
        claims.pop(name, None)
    return jwt.encode(claims, key or PRIVATE_KEY, algorithm=alg, headers={"kid": "test-key"})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def auth_headers(user):
    """Headers for a request made by `user` (a User row that has an auth_id)."""
    return bearer(make_token(user.auth_id, user.email))
