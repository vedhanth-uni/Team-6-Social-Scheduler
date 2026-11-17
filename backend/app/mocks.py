"""Stand-ins for code other teammates are writing.
Replace each function's body (or import the real one) and keep the signature.
"""
import uuid
from datetime import datetime, timedelta, timezone

from app.schemas.event import EventOut


def send_friend_request_email(receiver_id: uuid.UUID, sender_username: str) -> None:
    """MOCK for the email-invite teammate's function. Confirm the real signature with them."""
    print(f"[MOCK EMAIL] to user {receiver_id}: {sender_username} sent you a friend request")


def fetch_user_events(user_id: uuid.UUID) -> list[EventOut]:
    """MOCK for the events/schedule feature. Ignores user_id and returns fake data."""
    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return [
        EventOut(id=1, title="Study group", start_time=start + timedelta(days=1),
                 end_time=start + timedelta(days=1, hours=2), is_private=False),
        EventOut(id=2, title="Doctor appointment", start_time=start + timedelta(days=2),
                 end_time=start + timedelta(days=2, hours=1), is_private=True),
        EventOut(id=3, title="Club meeting", start_time=start + timedelta(days=3),
                 end_time=start + timedelta(days=3, hours=1), is_private=False),
    ]