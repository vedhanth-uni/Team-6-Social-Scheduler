# Run from the backend/ folder:  python -m pytest
# Each test gets a fresh in-memory SQLite DB, so tests never touch scheduler.db.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers tables)
from app.database import get_session
from app.main import app
from app.models.user import User


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def users(session):
    alice = User(email="alice@umass.edu", display_name="Alice")
    bob = User(email="bob@umass.edu", display_name="Bob")
    carol = User(email="carol@umass.edu", display_name="Carol")
    session.add_all([alice, bob, carol])
    session.commit()
    return alice, bob, carol


def h(user):
    return {"X-User-Id": str(user.id)}


def make_cal(client, user, name="Classes"):
    r = client.post("/calendars", json={"name": name}, headers=h(user))
    assert r.status_code == 201
    return r.json()


# ---------- calendars ----------

def test_create_and_first_is_primary(client, users):
    alice, *_ = users
    first = make_cal(client, alice, "Classes")
    second = make_cal(client, alice, "Gym")
    assert first["is_primary"] is True
    assert second["is_primary"] is False
    assert first["owner_id"] == alice.id
    assert first["my_access"] == "owner"


def test_unknown_user_rejected(client, users):
    r = client.post("/calendars", json={"name": "x"}, headers={"X-User-Id": "999"})
    assert r.status_code == 401


def test_stranger_cannot_see_calendar(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    assert client.get(f"/calendars/{cal['id']}", headers=h(bob)).status_code == 404


def test_patch_only_changes_sent_fields(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    r = client.patch(f"/calendars/{cal['id']}", json={"color": "#9ED05C"}, headers=h(alice))
    assert r.status_code == 200
    assert r.json()["color"] == "#9ED05C"
    assert r.json()["name"] == "Classes"


def test_soft_delete_hides_calendar(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    assert client.delete(f"/calendars/{cal['id']}", headers=h(alice)).status_code == 204
    assert client.get(f"/calendars/{cal['id']}", headers=h(alice)).status_code == 404
    assert client.get("/calendars", headers=h(alice)).json() == []


# ---------- sharing ----------

def test_share_shows_up_in_list(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    r = client.post(f"/calendars/{cal['id']}/shares",
                    json={"email": "bob@umass.edu", "permission": "viewer", "relationship": "close_friend"},
                    headers=h(alice))
    assert r.status_code == 201
    assert r.json()["user_id"] == bob.id

    mine = client.get("/calendars", headers=h(bob)).json()
    assert [(c["id"], c["my_access"]) for c in mine] == [(cal["id"], "viewer")]


def test_reshare_updates_instead_of_duplicating(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    url = f"/calendars/{cal['id']}/shares"
    client.post(url, json={"email": "bob@umass.edu"}, headers=h(alice))
    r = client.post(url, json={"email": "bob@umass.edu", "permission": "editor"}, headers=h(alice))
    assert r.status_code == 200
    shares = client.get(url, headers=h(alice)).json()
    assert len(shares) == 1
    assert shares[0]["permission"] == "editor"


def test_viewer_cannot_edit_but_editor_can(client, users):
    alice, bob, carol = users
    cal = make_cal(client, alice)
    url = f"/calendars/{cal['id']}/shares"
    client.post(url, json={"email": "bob@umass.edu", "permission": "viewer"}, headers=h(alice))
    client.post(url, json={"email": "carol@umass.edu", "permission": "editor"}, headers=h(alice))

    assert client.patch(f"/calendars/{cal['id']}", json={"name": "x"}, headers=h(bob)).status_code == 403
    assert client.patch(f"/calendars/{cal['id']}", json={"name": "x"}, headers=h(carol)).status_code == 200


def test_only_owner_can_delete_or_share(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    client.post(f"/calendars/{cal['id']}/shares",
                json={"email": "bob@umass.edu", "permission": "editor"}, headers=h(alice))
    assert client.delete(f"/calendars/{cal['id']}", headers=h(bob)).status_code == 403
    r = client.post(f"/calendars/{cal['id']}/shares",
                    json={"email": "carol@umass.edu"}, headers=h(bob))
    assert r.status_code == 403


def test_share_errors(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    url = f"/calendars/{cal['id']}/shares"
    assert client.post(url, json={"email": "nobody@umass.edu"}, headers=h(alice)).status_code == 404
    assert client.post(url, json={"email": "alice@umass.edu"}, headers=h(alice)).status_code == 400
    assert client.post(url, json={"email": "bob@umass.edu", "permission": "admin"},
                       headers=h(alice)).status_code == 422


def test_owner_removes_share_and_user_can_leave(client, users):
    alice, bob, carol = users
    cal = make_cal(client, alice)
    url = f"/calendars/{cal['id']}/shares"
    client.post(url, json={"email": "bob@umass.edu"}, headers=h(alice))
    client.post(url, json={"email": "carol@umass.edu"}, headers=h(alice))

    # owner kicks bob
    assert client.delete(f"{url}/{bob.id}", headers=h(alice)).status_code == 204
    assert client.get(f"/calendars/{cal['id']}", headers=h(bob)).status_code == 404
    # carol leaves on her own
    assert client.delete(f"{url}/{carol.id}", headers=h(carol)).status_code == 204
    assert client.get("/calendars", headers=h(carol)).json() == []
