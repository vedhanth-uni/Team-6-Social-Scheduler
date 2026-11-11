# the actual email content for friend requests. kept apart from the router so it's easy to reword.
# names come from users so they get html-escaped before going into the html version.

from html import escape
from urllib.parse import urlencode

from app.config import settings
from app.services.email import Email

LEVEL_LABEL = {"close": "close friend", "professional": "professional"}


def respond_link(token: str, action: str) -> str:
    # points at the frontend page, which makes the api call with the logged-in session
    return f"{settings.FRONTEND_URL}/friends/respond?{urlencode({'token': token, 'action': action})}"


def friend_request_email(*, to: str, sender_name: str, sender_email: str, level: str,
                         token: str, ttl_days: int) -> Email:
    label = LEVEL_LABEL[level]
    accept = respond_link(token, "accept")
    decline = respond_link(token, "decline")
    subject = f"{sender_name} wants to connect on Social Scheduler"

    text = (
        f"{sender_name} ({sender_email}) sent you a friend request as a {label} connection.\n\n"
        f"Accept:  {accept}\n"
        f"Decline: {decline}\n\n"
        f"You'll need to be logged in. This link expires in {ttl_days} days.\n"
        f"You can also accept or decline it from the Friends section of the app.\n"
    )

    n, e, l = escape(sender_name), escape(sender_email), escape(label)
    html = f"""\
<div style="font-family:system-ui,-apple-system,sans-serif;max-width:480px;margin:0 auto;color:#1f2933">
  <h2 style="margin-bottom:4px">New friend request</h2>
  <p><strong>{n}</strong> ({e}) wants to connect with you as a <strong>{l}</strong> connection.</p>
  <p style="margin:24px 0">
    <a href="{escape(accept)}" style="background:#2f855a;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;margin-right:8px">Accept</a>
    <a href="{escape(decline)}" style="background:#e2e8f0;color:#1f2933;padding:10px 18px;border-radius:6px;text-decoration:none">Decline</a>
  </p>
  <p style="font-size:13px;color:#52606d">You'll need to be logged in. This link expires in {ttl_days} days.
  You can also respond from the Friends section of the app.</p>
</div>"""
    return Email(to=to, subject=subject, text=text, html=html)


def request_accepted_email(*, to: str, accepter_name: str, level: str) -> Email:
    subject = f"{accepter_name} accepted your friend request"
    what = "close friends" if level == "close" else "professional contacts"
    text = f"{accepter_name} accepted your friend request. You're now connected as {what}.\n"
    html = f"""\
<div style="font-family:system-ui,-apple-system,sans-serif;max-width:480px;margin:0 auto;color:#1f2933">
  <p>{escape(text.strip())}</p>
  <p><a href="{escape(settings.FRONTEND_URL)}/Dash">Open Social Scheduler</a></p>
</div>"""
    return Email(to=to, subject=subject, text=text, html=html)
