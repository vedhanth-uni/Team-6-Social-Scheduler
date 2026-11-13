# Run from the backend/ folder:  python -m pytest tests/test_friends.py
# Emails are captured in a list instead of being sent, so we can pull the token out of the link.

import re
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers tables)
from app.database import get_session
from app.main import app
from app.models.friend import FriendRequest
from app.models.timeutil import utcnow
from app.models.user import User
from tests.auth_helpers import auth_headers
from app.services import email as email_service


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(email_service, "sender", sent.append)
    return sent


@pytest.fixture
def client(session, outbox):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def users(session):
    alice = User(auth_id="auth-alice", email="alice@umass.edu", display_name="Alice")
    bob = User(auth_id="auth-bob", email="bob@umass.edu", display_name="Bob")
    carol = User(auth_id="auth-carol", email="carol@umass.edu", display_name="Carol")
    session.add_all([alice, bob, carol])
    session.commit()
    return alice, bob, carol


h = auth_headers  # a real signed Supabase-style token for that user


def send(client, frm, to, level="close"):
    return client.post("/friend-requests", json={"email": to.email, "level": level}, headers=h(frm))


def token_from(mail, action="accept"):
    link = re.search(rf"https?://\S+action={action}\S*", mail.text).group(0)
    return parse_qs(urlparse(link).query)["token"][0]


# ---------- sending ----------

def test_send_creates_request_and_emails_recipient(client, users, outbox):
    alice, bob, _ = users
    r = send(client, alice, bob, "professional")
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["level"] == "professional"
    assert body["sender"]["id"] == alice.id and body["recipient"]["id"] == bob.id

    assert len(outbox) == 1
    mail = outbox[0]
    assert mail.to == "bob@umass.edu"
    assert "Alice" in mail.subject
    assert "/friends/respond?" in mail.text and "action=accept" in mail.text and "action=decline" in mail.text
    assert "professional" in mail.text


def test_unknown_email_says_user_doesnt_exist(client, users, outbox):
    alice, *_ = users
    r = client.post("/friend-requests", json={"email": "nobody@umass.edu", "level": "close"}, headers=h(alice))
    assert r.status_code == 404
    assert "No user" in r.json()["detail"]
    assert outbox == []


def test_cant_friend_yourself(client, users):
    alice, *_ = users
    assert send(client, alice, alice).status_code == 400


def test_bad_level_rejected(client, users):
    alice, bob, _ = users
    assert send(client, alice, bob, "temp").status_code == 422


def test_duplicate_outgoing_request_blocked(client, users):
    alice, bob, _ = users
    assert send(client, alice, bob).status_code == 201
    assert send(client, alice, bob).status_code == 409


def test_reverse_request_blocked_while_one_is_pending(client, users):
    # the "i send close, you send professional" case -- second one is refused, so nothing can overwrite
    alice, bob, _ = users
    assert send(client, alice, bob, "close").status_code == 201
    r = send(client, bob, alice, "professional")
    assert r.status_code == 409
    assert "already sent you" in r.json()["detail"]


def test_cant_request_existing_friend(client, users, outbox):
    alice, bob, _ = users
    send(client, alice, bob)
    client.post("/friend-requests/respond", json={"token": token_from(outbox[0]), "action": "accept"}, headers=h(bob))
    r = send(client, bob, alice, "professional")
    assert r.status_code == 409
    assert "already friends" in r.json()["detail"]


# ---------- in-app accept / decline / cancel ----------

def test_accept_in_app_creates_friendship_both_ways(client, users, outbox):
    alice, bob, _ = users
    req = send(client, alice, bob, "close").json()

    incoming = client.get("/friend-requests?direction=incoming", headers=h(bob)).json()
    assert [r["id"] for r in incoming] == [req["id"]]
    outgoing = client.get("/friend-requests?direction=outgoing", headers=h(alice)).json()
    assert [r["id"] for r in outgoing] == [req["id"]]

    r = client.post(f"/friend-requests/{req['id']}/accept", headers=h(bob))
    assert r.status_code == 200 and r.json()["status"] == "accepted"

    a_friends = client.get("/friends", headers=h(alice)).json()
    b_friends = client.get("/friends", headers=h(bob)).json()
    assert [(f["user"]["id"], f["level"]) for f in a_friends] == [(bob.id, "close")]
    assert [(f["user"]["id"], f["level"]) for f in b_friends] == [(alice.id, "close")]

    # sender gets told
    assert outbox[-1].to == "alice@umass.edu"
    assert "accepted" in outbox[-1].subject
    # and nothing is pending anymore
    assert client.get("/friend-requests?direction=incoming", headers=h(bob)).json() == []


def test_only_recipient_can_accept(client, users):
    alice, bob, carol = users
    req = send(client, alice, bob).json()
    assert client.post(f"/friend-requests/{req['id']}/accept", headers=h(alice)).status_code == 404
    assert client.post(f"/friend-requests/{req['id']}/accept", headers=h(carol)).status_code == 404


def test_decline_does_not_notify_sender(client, users, outbox):
    alice, bob, _ = users
    req = send(client, alice, bob).json()
    r = client.post(f"/friend-requests/{req['id']}/decline", headers=h(bob))
    assert r.json()["status"] == "declined"
    assert len(outbox) == 1  # just the original request email
    assert client.get("/friends", headers=h(alice)).json() == []
    # after a decline, either side can try again
    assert send(client, bob, alice, "professional").status_code == 201


def test_cant_respond_twice(client, users):
    alice, bob, _ = users
    req = send(client, alice, bob).json()
    client.post(f"/friend-requests/{req['id']}/accept", headers=h(bob))
    r = client.post(f"/friend-requests/{req['id']}/decline", headers=h(bob))
    assert r.status_code == 409


def test_sender_can_cancel(client, users, outbox):
    alice, bob, _ = users
    req = send(client, alice, bob).json()
    assert client.delete(f"/friend-requests/{req['id']}", headers=h(bob)).status_code == 404  # not bob's to cancel
    assert client.delete(f"/friend-requests/{req['id']}", headers=h(alice)).status_code == 204
    # the link in the email is dead now
    r = client.post("/friend-requests/respond", json={"token": token_from(outbox[0]), "action": "accept"}, headers=h(bob))
    assert r.status_code == 409
    assert send(client, alice, bob).status_code == 201


# ---------- email link (token) ----------

def test_email_accept_link_works_when_logged_in_as_recipient(client, users, outbox):
    alice, bob, _ = users
    send(client, alice, bob, "professional")
    token = token_from(outbox[0])

    look = client.post("/friend-requests/lookup", json={"token": token}, headers=h(bob))
    assert look.status_code == 200
    assert look.json()["sender"]["display_name"] == "Alice"

    r = client.post("/friend-requests/respond", json={"token": token, "action": "accept"}, headers=h(bob))
    assert r.status_code == 200 and r.json()["status"] == "accepted"
    assert client.get("/friends", headers=h(bob)).json()[0]["level"] == "professional"


def test_email_decline_link(client, users, outbox):
    alice, bob, _ = users
    send(client, alice, bob)
    r = client.post("/friend-requests/respond",
                    json={"token": token_from(outbox[0], "decline"), "action": "decline"}, headers=h(bob))
    assert r.json()["status"] == "declined"


def test_email_link_needs_login(client, users, outbox):
    alice, bob, _ = users
    send(client, alice, bob)
    r = client.post("/friend-requests/respond", json={"token": token_from(outbox[0]), "action": "accept"})
    assert r.status_code in (401, 422)  # no user header at all
    assert client.get("/friends", headers=h(bob)).json() == []


def test_email_link_wrong_account(client, users, outbox):
    alice, bob, carol = users
    send(client, alice, bob)
    r = client.post("/friend-requests/respond", json={"token": token_from(outbox[0]), "action": "accept"}, headers=h(carol))
    assert r.status_code == 403
    assert "different account" in r.json()["detail"]


def test_bad_token(client, users):
    _, bob, _ = users
    r = client.post("/friend-requests/respond", json={"token": "nope", "action": "accept"}, headers=h(bob))
    assert r.status_code == 404


def test_token_is_not_stored_in_plain_text(client, users, session, outbox):
    alice, bob, _ = users
    send(client, alice, bob)
    token = token_from(outbox[0])
    row = session.exec(models.FriendRequest.__table__.select()).first()
    assert token not in row.token_hash


def test_expired_link(client, users, session, outbox):
    alice, bob, _ = users
    req = send(client, alice, bob).json()
    row = session.get(FriendRequest, req["id"])
    row.expires_at = utcnow() - timedelta(minutes=1)
    session.add(row)
    session.commit()

    r = client.post("/friend-requests/respond", json={"token": token_from(outbox[0]), "action": "accept"}, headers=h(bob))
    assert r.status_code == 410
    # expired ones drop out of the pending lists and don't block a fresh request
    assert client.get("/friend-requests?direction=incoming", headers=h(bob)).json() == []
    assert send(client, alice, bob).status_code == 201


# ---------- unfriending ----------

def test_unfriend_from_either_side_then_rerequest_with_new_level(client, users):
    alice, bob, _ = users
    req = send(client, alice, bob, "professional").json()
    client.post(f"/friend-requests/{req['id']}/accept", headers=h(bob))

    assert client.delete(f"/friends/{alice.id}", headers=h(bob)).status_code == 204
    assert client.get("/friends", headers=h(alice)).json() == []
    assert client.delete(f"/friends/{alice.id}", headers=h(bob)).status_code == 404

    # changing level = remove + send a new request
    req2 = send(client, alice, bob, "close").json()
    client.post(f"/friend-requests/{req2['id']}/accept", headers=h(bob))
    assert client.get("/friends", headers=h(alice)).json()[0]["level"] == "close"


def test_email_failure_does_not_break_request(client, users, monkeypatch):
    alice, bob, _ = users

    def boom(_):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(email_service, "sender", boom)
    assert send(client, alice, bob).status_code == 201


def test_display_name_is_escaped_in_html_email(client, session, outbox):
    evil = User(auth_id="auth-evil", email="evil@umass.edu", display_name="<script>x</script>")
    bob = User(auth_id="auth-bob", email="bob@umass.edu", display_name="Bob")
    session.add_all([evil, bob])
    session.commit()
    send(client, evil, bob)
    assert "<script>" not in outbox[0].html


# ---------- gmail sending (fake smtp server, nothing really goes out) ----------

def test_gmail_send_uses_starttls_and_app_password(monkeypatch):
    calls = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            calls["server"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def starttls(self, context=None):
            calls["tls"] = True

        def login(self, user, pw):
            calls["login"] = (user, pw)

        def send_message(self, em):
            calls["from"], calls["to"], calls["subject"] = em["From"], em["To"], em["Subject"]

    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_service.settings, "GMAIL_ADDRESS", "team6.scheduler@gmail.com")
    monkeypatch.setattr(email_service.settings, "GMAIL_APP_PASSWORD", "abcdefghijklmnop")

    email_service.gmail_send(email_service.Email(to="bob@umass.edu", subject="hi", text="hello", html="<p>hello</p>"))

    assert calls["server"] == ("smtp.gmail.com", 587)
    assert calls["tls"] is True
    assert calls["login"] == ("team6.scheduler@gmail.com", "abcdefghijklmnop")
    assert "team6.scheduler@gmail.com" in calls["from"] and "Social Scheduler" in calls["from"]
    assert calls["to"] == "bob@umass.edu"
