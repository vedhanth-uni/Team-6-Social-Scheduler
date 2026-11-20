# the database side of the friends panel: accept, decline, unfriend

import pytest
from sqlmodel import select

from app.models.friendships import STATUS_ACCEPTED, STATUS_PENDING, Friendship


@pytest.fixture
def alice(make_profile):
    return make_profile("alice")


@pytest.fixture
def bob(make_profile):
    return make_profile("bob")


def send_request(client, auth_as, sender, recipient, level="close") -> int:
    auth_as(sender)
    res = client.post("/friend-requests", json={"username": recipient.username, "level": level})
    assert res.status_code == 201, res.text
    return res.json()["id"]


def all_rows(session):
    session.expire_all()
    return session.exec(select(Friendship)).all()


def test_incoming_requests_lists_pending_newest_first(client, auth_as, alice, bob, make_profile):
    carol = make_profile("carol")
    send_request(client, auth_as, alice, carol)
    send_request(client, auth_as, bob, carol, level="professional")

    auth_as(carol)
    res = client.get("/friend-requests", params={"direction": "incoming"})

    assert res.status_code == 200
    assert [(r["sender"]["username"], r["level"]) for r in res.json()] == [
        ("bob", "professional"),
        ("alice", "close"),
    ]


def test_accept_request_marks_row_accepted_and_both_see_friend(client, auth_as, session, alice, bob):
    request_id = send_request(client, auth_as, alice, bob, level="professional")

    auth_as(bob)
    res = client.post(f"/friend-requests/{request_id}/accept")

    assert res.status_code == 200
    assert res.json()["status"] == STATUS_ACCEPTED
    (row,) = all_rows(session)
    assert row.status == STATUS_ACCEPTED
    assert client.get("/friend-requests").json() == []
    assert [(f["user"]["username"], f["level"]) for f in client.get("/friends").json()] == [("alice", "professional")]
    auth_as(alice)
    assert [f["user"]["username"] for f in client.get("/friends").json()] == ["bob"]


def test_decline_request_deletes_row_and_sender_can_ask_again(client, auth_as, session, alice, bob):
    request_id = send_request(client, auth_as, alice, bob)

    auth_as(bob)
    res = client.post(f"/friend-requests/{request_id}/decline")

    assert res.status_code == 200
    assert res.json()["status"] == "declined"
    assert all_rows(session) == []
    assert client.get("/friends").json() == []
    send_request(client, auth_as, alice, bob)
    assert [row.status for row in all_rows(session)] == [STATUS_PENDING]


def test_accept_request_already_declined_returns_404(client, auth_as, alice, bob):
    # e.g. declined from the email link while the panel was still showing it
    request_id = send_request(client, auth_as, alice, bob)
    auth_as(bob)
    client.post(f"/friend-requests/{request_id}/decline")

    res = client.post(f"/friend-requests/{request_id}/accept")

    assert res.status_code == 404


def test_accept_request_by_non_recipient_returns_404(client, auth_as, session, alice, bob):
    request_id = send_request(client, auth_as, alice, bob)

    auth_as(alice)
    res = client.post(f"/friend-requests/{request_id}/accept")

    assert res.status_code == 404
    assert [row.status for row in all_rows(session)] == [STATUS_PENDING]


def test_remove_friend_deletes_row_for_both_sides(client, auth_as, session, alice, bob):
    request_id = send_request(client, auth_as, alice, bob)
    auth_as(bob)
    client.post(f"/friend-requests/{request_id}/accept")

    res = client.delete(f"/friends/{alice.id}")

    assert res.status_code == 204
    assert all_rows(session) == []
    assert client.get("/friends").json() == []
    auth_as(alice)
    assert client.get("/friends").json() == []


def test_remove_friend_with_pending_request_returns_404_and_keeps_it(client, auth_as, session, alice, bob):
    send_request(client, auth_as, alice, bob)

    auth_as(bob)
    res = client.delete(f"/friends/{alice.id}")

    assert res.status_code == 404
    assert [row.status for row in all_rows(session)] == [STATUS_PENDING]

