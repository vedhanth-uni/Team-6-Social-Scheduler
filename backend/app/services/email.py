# sending email through gmail. one function, send_email(), everything else calls that.
# if GMAIL_ADDRESS / GMAIL_APP_PASSWORD aren't set the email gets printed to the console instead,
# so you can still click the links in dev. tests swap `sender` for a fake that records what was sent.

import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr

from app.config import settings

log = logging.getLogger("app.email")

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587  # STARTTLS


@dataclass
class Email:
    to: str
    subject: str
    text: str
    html: str | None = None


def gmail_send(msg: Email) -> None:
    em = EmailMessage()
    # gmail only lets you send as the account you logged in with, so From is always that address
    em["From"] = formataddr((settings.EMAIL_FROM_NAME, settings.GMAIL_ADDRESS))
    em["To"] = msg.to
    em["Subject"] = msg.subject
    em.set_content(msg.text)
    if msg.html:
        em.add_alternative(msg.html, subtype="html")

    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=15) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
        s.send_message(em)


def console_send(msg: Email) -> None:
    print(f"\n----- EMAIL (gmail not configured, not actually sent) -----\n"
          f"To: {msg.to}\nSubject: {msg.subject}\n\n{msg.text}\n"
          f"-----------------------------------------------------------\n", flush=True)


sender = gmail_send if settings.gmail_enabled else console_send


def send_email(msg: Email) -> None:
    # runs as a background task after the response goes out, so a slow/broken smtp connection
    # never fails the api call. failures just get logged.
    try:
        sender(msg)
    except Exception:
        log.exception("failed to send email to %s", msg.to)
