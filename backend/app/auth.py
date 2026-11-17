import uuid

from fastapi import Header

# TEMPORARY: replace with real Supabase token verification.
# This trusts the caller completely, so anyone could impersonate anyone.
# It must never be deployed.
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_current_user_id(
    x_dev_user_id: uuid.UUID | None = Header(default=None),
) -> uuid.UUID:
    """Return the ID of the logged-in user.

    For now: the X-Dev-User-Id header if present (so you can pretend to be
    different users), otherwise a fixed ID. Later: verify the Authorization
    token and return its `sub` claim. Endpoints only depend on this function,
    so swapping the implementation won't change them.
    """
    return x_dev_user_id or DEV_USER_ID