# same setup as test_calendars

from tests.test_calendars import client, h, make_cal, session, users  # noqa: F401

WEEK = {"start": "2026-10-26T00:00:00-04:00", "end": "2026-11-02T00:00:00-05:00"}


def make_event(client, user, cal_id, **kw):
    body = {
        "title": "CS 320",
        "start": "2026-10-26T10:00:00",
        "end": "2026-10-26T11:15:00",
        **kw,
    }
    r = client.post(f"/calendars/{cal_id}/events", json=body, headers=h(user))
    assert r.status_code == 201, r.text
    return r.json()


def share(client, owner, cal_id, email, permission="viewer"):
    r = client.post(f"/calendars/{cal_id}/shares",
                    json={"email": email, "permission": permission}, headers=h(owner))
    assert r.status_code in (200, 201)


def test_create_and_get_event(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"])
    assert ev["timezone"] == "America/New_York"  # should use the calendars timezone
    assert ev["start"] == "2026-10-26T10:00:00-04:00"
    assert ev["can_edit"] is True

    r = client.get(f"/events/{ev['id']}", headers=h(alice))
    assert r.status_code == 200
    assert r.json()["title"] == "CS 320"


def test_end_before_start_rejected(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    r = client.post(f"/calendars/{cal['id']}/events",
                    json={"title": "x", "start": "2026-10-26T11:00:00", "end": "2026-10-26T10:00:00"},
                    headers=h(alice))
    assert r.status_code == 422


def test_all_day_event_defaults_to_one_day(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"], start="2026-10-31T15:00:00", end=None, all_day=True)
    assert ev["start"] == "2026-10-31T00:00:00-04:00"
    assert ev["end"] == "2026-11-01T00:00:00-04:00"


def test_edit_only_changes_sent_fields_and_keeps_length(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"])
    r = client.patch(f"/events/{ev['id']}", json={"start": "2026-10-27T14:00:00"}, headers=h(alice))
    assert r.status_code == 200
    assert r.json()["title"] == "CS 320"
    assert r.json()["end"] == "2026-10-27T15:15:00-04:00"  # still 75 mins


def test_delete_hides_event(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"])
    assert client.delete(f"/events/{ev['id']}", headers=h(alice)).status_code == 204
    assert client.get(f"/events/{ev['id']}", headers=h(alice)).status_code == 404
    assert client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(alice)).json() == []


def test_viewer_cant_add_or_edit_but_editor_can(client, users):
    alice, bob, carol = users
    cal = make_cal(client, alice)
    share(client, alice, cal["id"], "bob@umass.edu", "viewer")
    share(client, alice, cal["id"], "carol@umass.edu", "editor")
    ev = make_event(client, alice, cal["id"], visibility="professional")

    body = {"title": "x", "start": "2026-10-26T10:00:00", "end": "2026-10-26T11:00:00"}
    assert client.post(f"/calendars/{cal['id']}/events", json=body, headers=h(bob)).status_code == 403
    assert client.patch(f"/events/{ev['id']}", json={"title": "y"}, headers=h(bob)).status_code == 403
    assert client.post(f"/calendars/{cal['id']}/events", json=body, headers=h(carol)).status_code == 201
    assert client.patch(f"/events/{ev['id']}", json={"title": "y"}, headers=h(carol)).status_code == 200


def test_weekly_event_shows_every_mwf(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    make_event(client, alice, cal["id"], rrule="FREQ=WEEKLY;BYDAY=MO,WE,FR")
    occ = client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(alice)).json()
    assert [o["start"][:10] for o in occ] == ["2026-10-26", "2026-10-28", "2026-10-30"]
    assert all(o["is_recurring"] for o in occ)


def test_recurring_stays_same_local_time_after_dst(client, users):
    # clocks go back nov 1, should still be 10am
    alice, *_ = users
    cal = make_cal(client, alice)
    make_event(client, alice, cal["id"], rrule="FREQ=WEEKLY;BYDAY=MO")
    occ = client.get(f"/calendars/{cal['id']}/events",
                     params={"start": "2026-10-26T00:00:00Z", "end": "2026-11-03T00:00:00Z"},
                     headers=h(alice)).json()
    assert [o["start"] for o in occ] == ["2026-10-26T10:00:00-04:00", "2026-11-02T10:00:00-05:00"]


def test_rrule_until_stops_it(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    make_event(client, alice, cal["id"], rrule="FREQ=DAILY;UNTIL=20261027T235959")
    occ = client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(alice)).json()
    assert len(occ) == 2


def test_bad_rrule_rejected(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    for rule in ["FREQ=MINUTELY", "FREQ=WEEKLY;BYDAY=XX", "nonsense"]:
        r = client.post(f"/calendars/{cal['id']}/events",
                        json={"title": "x", "start": "2026-10-26T10:00:00",
                              "end": "2026-10-26T11:00:00", "rrule": rule},
                        headers=h(alice))
        assert r.status_code == 422, rule


def test_stop_repeating(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"], rrule="FREQ=DAILY")
    client.patch(f"/events/{ev['id']}", json={"rrule": None}, headers=h(alice))
    occ = client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(alice)).json()
    assert len(occ) == 1


def test_public_event_anyone_can_see_and_join(client, users):
    alice, bob, _ = users  # bob isnt shared on alices calendar
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"], visibility="public")
    make_event(client, alice, cal["id"], title="secret", visibility="private")

    assert client.get(f"/events/{ev['id']}", headers=h(bob)).status_code == 200
    occ = client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(bob)).json()
    assert [o["title"] for o in occ] == ["CS 320"]  # only the public one

    assert client.post(f"/events/{ev['id']}/join", headers=h(bob)).status_code == 201
    assert client.get(f"/events/{ev['id']}", headers=h(bob)).json()["joined"] is True


def test_stranger_cant_see_non_public(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"], visibility="professional")
    assert client.get(f"/events/{ev['id']}", headers=h(bob)).status_code == 404
    assert client.post(f"/events/{ev['id']}/join", headers=h(bob)).status_code == 404
    assert client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(bob)).status_code == 404


def test_viewer_sees_professional_not_private(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    share(client, alice, cal["id"], "bob@umass.edu", "viewer")
    pro = make_event(client, alice, cal["id"], title="standup", visibility="professional")
    priv = make_event(client, alice, cal["id"], title="dentist", visibility="private")

    occ = client.get(f"/calendars/{cal['id']}/events", params=WEEK, headers=h(bob)).json()
    assert [o["title"] for o in occ] == ["standup"]
    assert client.post(f"/events/{pro['id']}/join", headers=h(bob)).status_code == 201
    assert client.post(f"/events/{priv['id']}/join", headers=h(bob)).status_code == 404


def test_join_twice_and_leave(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    ev = make_event(client, alice, cal["id"], visibility="public")
    url = f"/events/{ev['id']}/join"
    assert client.post(url, headers=h(bob)).status_code == 201
    assert client.post(url, headers=h(bob)).status_code == 200  # no duplicate
    assert client.delete(url, headers=h(bob)).status_code == 204
    assert client.delete(url, headers=h(bob)).status_code == 404
