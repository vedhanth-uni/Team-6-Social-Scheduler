# Same setup as test_calendars / test_events. Run from backend/:  python -m pytest

from tests.test_calendars import client, h, make_cal, session, users  # noqa: F401
from tests.test_events import share

from app.services.ics_import import normalize_rrule


def ics(*events: str) -> bytes:
    body = "\r\n".join(events)
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n" + body + "\r\nEND:VCALENDAR\r\n"
    ).encode()


def vevent(uid, title, *lines):
    return "\r\n".join(["BEGIN:VEVENT", f"UID:{uid}", f"SUMMARY:{title}", *lines, "END:VEVENT"])


def upload(client, user, cal_id, content, **params):
    return client.post(
        f"/calendars/{cal_id}/import",
        files={"file": ("calendar.ics", content, "text/calendar")},
        params=params,
        headers=h(user),
    )


def window(client, user, cal_id, start, end):
    r = client.get(f"/calendars/{cal_id}/events", params={"start": start, "end": end}, headers=h(user))
    assert r.status_code == 200, r.text
    return r.json()


# ---------- happy path ----------

def test_import_creates_events_through_the_events_api(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    content = ics(
        vevent("a1", "CS 320", "DTSTART;TZID=America/New_York:20261105T100000",
               "DTEND;TZID=America/New_York:20261105T111500", "LOCATION:Room 101",
               "DESCRIPTION:Bring laptop"),
        vevent("a2", "Utc event", "DTSTART:20261106T150000Z", "DTEND:20261106T160000Z"),
    )
    r = upload(client, alice, cal["id"], content)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["created"] == 2 and out["failed"] == [] and out["duplicates"] == 0

    ev = client.get(f"/events/{out['event_ids'][0]}", headers=h(alice)).json()
    assert ev["title"] == "CS 320"
    assert ev["location"] == "Room 101"
    assert ev["description"] == "Bring laptop"
    assert ev["timezone"] == "America/New_York"
    assert ev["start"] == "2026-11-05T10:00:00-05:00"
    assert ev["visibility"] == "private"

    # the one-off utc event is shown in the calendar's timezone: 15:00Z = 10:00 EST
    utc_ev = client.get(f"/events/{out['event_ids'][1]}", headers=h(alice)).json()
    assert utc_ev["timezone"] == "America/New_York"
    assert utc_ev["start"] == "2026-11-06T10:00:00-05:00"


def test_all_day_events_land_on_the_right_date(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)  # calendar tz is America/New_York (west of utc)
    content = ics(
        vevent("d1", "Conference", "DTSTART;VALUE=DATE:20261110", "DTEND;VALUE=DATE:20261113"),
        vevent("d2", "Birthday", "DTSTART;VALUE=DATE:20261120"),
    )
    out = upload(client, alice, cal["id"], content).json()
    assert out["created"] == 2
    conf = client.get(f"/events/{out['event_ids'][0]}", headers=h(alice)).json()
    assert conf["all_day"] is True
    assert conf["start"].startswith("2026-11-10T00:00:00")
    assert conf["end"].startswith("2026-11-13T00:00:00")
    bday = client.get(f"/events/{out['event_ids'][1]}", headers=h(alice)).json()
    assert bday["start"].startswith("2026-11-20T00:00:00")
    assert bday["end"].startswith("2026-11-21T00:00:00")


def test_recurring_event_keeps_local_hour_across_dst(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    # dst ends Sun 2026-11-01. A 9am class must stay 9am local on both sides of it.
    content = ics(vevent(
        "r1", "Weekly class",
        "DTSTART;TZID=America/New_York:20261026T090000",
        "DTEND;TZID=America/New_York:20261026T102000",
        "RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20261116T140000Z",  # utc UNTIL, like google writes
    ))
    out = upload(client, alice, cal["id"], content).json()
    assert out["created"] == 1 and out["failed"] == []

    occ = window(client, alice, cal["id"], "2026-10-25T00:00:00-04:00", "2026-12-01T00:00:00-05:00")
    assert [o["start"] for o in occ] == [
        "2026-10-26T09:00:00-04:00",
        "2026-11-02T09:00:00-05:00",
        "2026-11-09T09:00:00-05:00",
        "2026-11-16T09:00:00-05:00",
    ]  # UNTIL is inclusive, so the 16th is the last one


def test_outlook_windows_timezone_name_is_mapped(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    vtz = (
        "BEGIN:VTIMEZONE\r\nTZID:Pacific Standard Time\r\n"
        "BEGIN:STANDARD\r\nDTSTART:16011104T020000\r\nRRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=11\r\n"
        "TZOFFSETFROM:-0700\r\nTZOFFSETTO:-0800\r\nEND:STANDARD\r\n"
        "BEGIN:DAYLIGHT\r\nDTSTART:16010311T020000\r\nRRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3\r\n"
        "TZOFFSETFROM:-0800\r\nTZOFFSETTO:-0700\r\nEND:DAYLIGHT\r\nEND:VTIMEZONE"
    )
    content = ics(vtz, vevent("o1", "From Outlook",
                              "DTSTART;TZID=Pacific Standard Time:20261105T100000",
                              "DTEND;TZID=Pacific Standard Time:20261105T110000"))
    out = upload(client, alice, cal["id"], content).json()
    assert out["created"] == 1 and out["warnings"] == []
    ev = client.get(f"/events/{out['event_ids'][0]}", headers=h(alice)).json()
    assert ev["timezone"] == "America/Los_Angeles"
    assert ev["start"] == "2026-11-05T10:00:00-08:00"


def test_floating_times_use_default_tz_param_or_calendar_tz(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    content = ics(vevent("f1", "Floating", "DTSTART:20261105T100000", "DTEND:20261105T110000"))
    a = upload(client, alice, cal["id"], content).json()
    ev = client.get(f"/events/{a['event_ids'][0]}", headers=h(alice)).json()
    assert ev["timezone"] == "America/New_York" and ev["start"] == "2026-11-05T10:00:00-05:00"

    cal2 = make_cal(client, alice, name="Other")
    b = upload(client, alice, cal2["id"], content, default_tz="Europe/Rome").json()
    ev = client.get(f"/events/{b['event_ids'][0]}", headers=h(alice)).json()
    assert ev["timezone"] == "Europe/Rome" and ev["start"] == "2026-11-05T10:00:00+01:00"


def test_visibility_param_applies_to_every_event(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    out = upload(client, alice, cal["id"],
                 ics(vevent("v1", "Open", "DTSTART:20261105T150000Z", "DTEND:20261105T160000Z")),
                 visibility="public").json()
    assert client.get(f"/events/{out['event_ids'][0]}", headers=h(alice)).json()["visibility"] == "public"
    r = upload(client, alice, cal["id"], ics(), visibility="secret")
    assert r.status_code == 422


# ---------- re-importing, skipping, failures ----------

def test_reimporting_the_same_file_does_not_duplicate(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    content = ics(
        vevent("a1", "One", "DTSTART:20261105T150000Z", "DTEND:20261105T160000Z"),
        vevent("a2", "Weekly", "DTSTART;TZID=America/New_York:20261026T090000",
               "DTEND;TZID=America/New_York:20261026T100000", "RRULE:FREQ=WEEKLY;COUNT=3"),
    )
    assert upload(client, alice, cal["id"], content).json()["created"] == 2
    again = upload(client, alice, cal["id"], content).json()
    assert again["created"] == 0 and again["duplicates"] == 2
    forced = upload(client, alice, cal["id"], content, skip_duplicates="false").json()
    assert forced["created"] == 2


def test_cancelled_overrides_and_exdates_are_reported_not_silently_dropped(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    content = ics(
        vevent("c1", "Cancelled", "STATUS:CANCELLED", "DTSTART:20261105T150000Z"),
        vevent("s1", "Series", "DTSTART:20261102T140000Z", "DTEND:20261102T150000Z",
               "RRULE:FREQ=WEEKLY;COUNT=4", "EXDATE:20261109T140000Z"),
        vevent("s1", "Series moved", "RECURRENCE-ID:20261116T140000Z",
               "DTSTART:20261116T160000Z", "DTEND:20261116T170000Z"),
    )
    out = upload(client, alice, cal["id"], content).json()
    assert out["created"] == 1
    reasons = " | ".join(s["reason"] for s in out["skipped"])
    assert "cancelled" in reasons and "recurring" in reasons
    assert any("excluded" in w["reason"] for w in out["warnings"])


def test_one_bad_event_does_not_block_the_others(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    content = ics(
        vevent("h1", "Hourly", "DTSTART:20261105T150000Z", "DTEND:20261105T153000Z",
               "RRULE:FREQ=HOURLY;COUNT=3"),  # events api only allows daily/weekly/monthly/yearly
        vevent("ok", "Fine", "DTSTART:20261106T150000Z", "DTEND:20261106T160000Z"),
    )
    out = upload(client, alice, cal["id"], content).json()
    assert out["created"] == 1
    assert len(out["failed"]) == 1 and out["failed"][0]["title"] == "Hourly"
    assert "FREQ" in out["failed"][0]["reason"]


def test_event_without_end_gets_one_hour_and_a_warning(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    out = upload(client, alice, cal["id"],
                 ics(vevent("z", "Reminder", "DTSTART:20261105T150000Z"))).json()
    assert out["created"] == 1 and "1 hour" in out["warnings"][0]["reason"]
    ev = client.get(f"/events/{out['event_ids'][0]}", headers=h(alice)).json()
    assert ev["start"] == "2026-11-05T10:00:00-05:00" and ev["end"] == "2026-11-05T11:00:00-05:00"


# ---------- permissions and bad input ----------

def test_only_owner_or_editor_can_import(client, users):
    alice, bob, carol = users
    cal = make_cal(client, alice)
    share(client, alice, cal["id"], "bob@umass.edu", "viewer")
    share(client, alice, cal["id"], "carol@umass.edu", "editor")
    content = ics(vevent("a", "Hi", "DTSTART:20261105T150000Z", "DTEND:20261105T160000Z"))
    assert upload(client, bob, cal["id"], content).status_code == 403
    assert upload(client, carol, cal["id"], content).json()["created"] == 1


def test_stranger_and_missing_calendar_get_404(client, users):
    alice, bob, _ = users
    cal = make_cal(client, alice)
    content = ics()
    assert upload(client, bob, cal["id"], content).status_code == 404
    assert upload(client, alice, 9999, content).status_code == 404


def test_garbage_file_and_bad_timezone_rejected(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    assert upload(client, alice, cal["id"], b"this is not a calendar").status_code == 422
    assert upload(client, alice, cal["id"], ics(), default_tz="Mars/Olympus").status_code == 422


def test_oversized_file_rejected(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    assert upload(client, alice, cal["id"], b"x" * (5 * 1024 * 1024 + 1)).status_code == 413


def test_missing_file_field_is_422(client, users):
    alice, *_ = users
    cal = make_cal(client, alice)
    assert client.post(f"/calendars/{cal['id']}/import", headers=h(alice)).status_code == 422


# ---------- rrule helper ----------

def test_normalize_rrule_converts_utc_until_to_local():
    # 04:59:59Z on Dec 31 is 23:59:59 on Dec 30 in New York (EST)
    assert normalize_rrule("FREQ=WEEKLY;UNTIL=20261231T045959Z", "America/New_York") == \
        "FREQ=WEEKLY;UNTIL=20261230T235959"
    assert normalize_rrule("RRULE:FREQ=DAILY;COUNT=3", "America/New_York") == "FREQ=DAILY;COUNT=3"
    assert normalize_rrule("FREQ=DAILY;UNTIL=20261231", "UTC") == "FREQ=DAILY;UNTIL=20261231"
