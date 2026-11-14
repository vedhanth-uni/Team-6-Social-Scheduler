from datetime import datetime, timedelta, timezone

import pytest

from app.services.ics_parser import ICSParseError, parse_ics

UTC = timezone.utc


def wrap(*events: str) -> str:
    body = "\r\n".join(events)
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n"
        + body
        + "\r\nEND:VCALENDAR\r\n"
    )


def test_utc_event_with_details():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:abc@example.com\r\nSUMMARY:CS320 Lecture\r\n"
        "DTSTART:20261105T150000Z\r\nDTEND:20261105T163000Z\r\n"
        "LOCATION:Room 101\r\nDESCRIPTION:Bring laptop\\, charger\r\nEND:VEVENT"
    )
    result = parse_ics(ics)
    assert result.skipped == []
    (e,) = result.events
    assert e.uid == "abc@example.com"
    assert e.title == "CS320 Lecture"
    assert e.start == datetime(2026, 11, 5, 15, 0, tzinfo=UTC)
    assert e.end == datetime(2026, 11, 5, 16, 30, tzinfo=UTC)
    assert e.location == "Room 101"
    assert e.description == "Bring laptop, charger"
    assert not e.all_day and e.rrule is None


def test_tzid_converted_to_utc():
    # 10:00 New York in November (EST, UTC-5) is 15:00 UTC.
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:tz1\r\nSUMMARY:Standup\r\n"
        "DTSTART;TZID=America/New_York:20261105T100000\r\n"
        "DTEND;TZID=America/New_York:20261105T103000\r\nEND:VEVENT"
    )
    (e,) = parse_ics(ics).events
    assert e.start == datetime(2026, 11, 5, 15, 0, tzinfo=UTC)
    assert e.end == datetime(2026, 11, 5, 15, 30, tzinfo=UTC)


def test_floating_time_uses_default_tz():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:f1\r\nSUMMARY:Floating\r\n"
        "DTSTART:20261105T100000\r\nDTEND:20261105T110000\r\nEND:VEVENT"
    )
    (utc_default,) = parse_ics(ics).events
    assert utc_default.start == datetime(2026, 11, 5, 10, 0, tzinfo=UTC)
    (ny,) = parse_ics(ics, default_tz="America/New_York").events
    assert ny.start == datetime(2026, 11, 5, 15, 0, tzinfo=UTC)


def test_all_day_end_is_exclusive_and_defaults_to_one_day():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:d1\r\nSUMMARY:Conference\r\n"
        "DTSTART;VALUE=DATE:20261110\r\nDTEND;VALUE=DATE:20261113\r\nEND:VEVENT",
        "BEGIN:VEVENT\r\nUID:d2\r\nSUMMARY:Birthday\r\n"
        "DTSTART;VALUE=DATE:20261120\r\nEND:VEVENT",
    )
    multi, single = parse_ics(ics).events
    assert multi.all_day and single.all_day
    assert multi.start == datetime(2026, 11, 10, tzinfo=UTC)
    assert multi.end == datetime(2026, 11, 13, tzinfo=UTC)
    assert single.end - single.start == timedelta(days=1)


def test_duration_instead_of_dtend():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:dur\r\nSUMMARY:Office hours\r\n"
        "DTSTART:20261105T150000Z\r\nDURATION:PT45M\r\nEND:VEVENT"
    )
    (e,) = parse_ics(ics).events
    assert e.end - e.start == timedelta(minutes=45)


def test_no_end_means_zero_length():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:z\r\nSUMMARY:Reminder\r\nDTSTART:20261105T150000Z\r\nEND:VEVENT"
    )
    (e,) = parse_ics(ics).events
    assert e.end == e.start


def test_recurrence_rule_exdate_and_override_are_preserved():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:r1\r\nSUMMARY:Weekly sync\r\n"
        "DTSTART:20261102T140000Z\r\nDTEND:20261102T150000Z\r\n"
        "RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=10\r\n"
        "EXDATE:20261109T140000Z\r\nEND:VEVENT",
        "BEGIN:VEVENT\r\nUID:r1\r\nSUMMARY:Weekly sync (moved)\r\n"
        "RECURRENCE-ID:20261116T140000Z\r\n"
        "DTSTART:20261116T160000Z\r\nDTEND:20261116T170000Z\r\nEND:VEVENT",
    )
    base, override = parse_ics(ics).events
    # The library may reorder the parts, so compare them as a set.
    assert set(base.rrule.split(";")) == {"FREQ=WEEKLY", "BYDAY=MO", "COUNT=10"}
    assert base.exdates == (datetime(2026, 11, 9, 14, 0, tzinfo=UTC),)
    assert override.uid == base.uid
    assert override.recurrence_id == datetime(2026, 11, 16, 14, 0, tzinfo=UTC)
    assert override.rrule is None


def test_cancelled_and_startless_events_are_skipped_not_fatal():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:c1\r\nSUMMARY:Cancelled\r\nSTATUS:CANCELLED\r\n"
        "DTSTART:20261105T150000Z\r\nEND:VEVENT",
        "BEGIN:VEVENT\r\nUID:n1\r\nSUMMARY:No start\r\nEND:VEVENT",
        "BEGIN:VEVENT\r\nUID:ok\r\nSUMMARY:Fine\r\nDTSTART:20261105T150000Z\r\nEND:VEVENT",
    )
    result = parse_ics(ics)
    assert [e.uid for e in result.events] == ["ok"]
    assert {s.reason for s in result.skipped} == {"cancelled", "missing or unreadable start time"}


def test_end_before_start_is_skipped():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:bad\r\nSUMMARY:Backwards\r\n"
        "DTSTART:20261105T160000Z\r\nDTEND:20261105T150000Z\r\nEND:VEVENT"
    )
    result = parse_ics(ics)
    assert result.events == []
    assert result.skipped[0].reason == "end is before start"


def test_missing_title_and_uid_get_defaults_and_uid_is_stable():
    ics = wrap("BEGIN:VEVENT\r\nDTSTART:20261105T150000Z\r\nEND:VEVENT")
    (a,) = parse_ics(ics).events
    (b,) = parse_ics(ics).events
    assert a.title == "(No title)"
    assert a.uid.startswith("generated-") and a.uid == b.uid


def test_accepts_bytes_and_unicode():
    ics = wrap(
        "BEGIN:VEVENT\r\nUID:u\r\nSUMMARY:Зустріч ☕\r\nDTSTART:20261105T150000Z\r\nEND:VEVENT"
    ).encode("utf-8")
    (e,) = parse_ics(ics).events
    assert e.title == "Зустріч ☕"


def test_empty_calendar_returns_no_events():
    result = parse_ics(wrap())
    assert result.events == [] and result.skipped == []


@pytest.mark.parametrize("garbage", [b"", b"hello world", b"<html></html>", b"\x00\x01\x02"])
def test_garbage_raises_ics_parse_error(garbage):
    with pytest.raises(ICSParseError):
        parse_ics(garbage)


def test_unknown_default_timezone_rejected():
    with pytest.raises(ValueError):
        parse_ics(wrap(), default_tz="Mars/Olympus")
