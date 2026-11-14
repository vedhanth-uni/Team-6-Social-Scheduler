from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from icalendar import Calendar

UTC = timezone.utc
UNTITLED = "(No title)"


class ICSParseError(ValueError):
    """The file is not a readable iCalendar file."""


@dataclass(frozen=True)
class ParsedEvent:
    uid: str
    title: str
    start: datetime
    end: datetime
    all_day: bool = False
    # Original timezone name from the file (e.g. "America/New_York", or
    # "Eastern Standard Time" from Outlook), "UTC" for Z times, or None for
    # floating / all-day events. Needed so recurring events keep their local
    # hour across daylight-saving changes.
    tzid: str | None = None
    description: str | None = None
    location: str | None = None
    rrule: str | None = None
    exdates: tuple[datetime, ...] = ()
    # Set when this VEVENT overrides one occurrence of a recurring event.
    recurrence_id: datetime | None = None


@dataclass(frozen=True)
class SkippedItem:
    uid: str | None
    title: str | None
    reason: str


@dataclass
class ParseResult:
    events: list[ParsedEvent] = field(default_factory=list)
    skipped: list[SkippedItem] = field(default_factory=list)


def _to_utc(value: datetime, default_tz: ZoneInfo | timezone) -> datetime:
    if value.tzinfo is None:  # floating time
        value = value.replace(tzinfo=default_tz)
    return value.astimezone(UTC)


def _day_start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


def _is_all_day(value) -> bool:
    # datetime is a subclass of date, so check datetime first.
    return isinstance(value, date) and not isinstance(value, datetime)


def _text(component, key: str) -> str | None:
    raw = component.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _decoded(component, key: str):
    """Return the decoded value of a property, or None if missing/unreadable."""
    if key not in component:
        return None
    try:
        return component.decoded(key)
    except Exception:
        return None


def _exdates(component, default_tz) -> tuple[datetime, ...]:
    raw = component.get("EXDATE")
    if raw is None:
        return ()
    groups = raw if isinstance(raw, list) else [raw]
    result: list[datetime] = []
    for group in groups:
        for item in getattr(group, "dts", []):
            value = item.dt
            result.append(_day_start(value) if _is_all_day(value) else _to_utc(value, default_tz))
    return tuple(result)


def _fallback_uid(title: str, start: datetime) -> str:
    digest = hashlib.sha1(f"{title}|{start.isoformat()}".encode()).hexdigest()[:16]
    return f"generated-{digest}"


def parse_ics(data: bytes | str, default_tz: str = "UTC") -> ParseResult:
    """Parse ICS content and return normalized events.

    Raises ICSParseError if the content is not a valid calendar at all.
    Individual bad or cancelled events do not raise; they are listed in
    `skipped` so one broken event can't block the rest of an import.
    """
    try:
        tz = ZoneInfo(default_tz)
    except Exception as exc:
        raise ValueError(f"Unknown timezone: {default_tz!r}") from exc

    try:
        calendar = Calendar.from_ical(data)
    except Exception as exc:
        raise ICSParseError("Could not read this file as an iCalendar (.ics) file") from exc

    if calendar.name != "VCALENDAR":
        raise ICSParseError("File does not contain a VCALENDAR")

    result = ParseResult()

    for component in calendar.walk("VEVENT"):
        uid = _text(component, "UID")
        title = _text(component, "SUMMARY") or UNTITLED

        if (_text(component, "STATUS") or "").upper() == "CANCELLED":
            result.skipped.append(SkippedItem(uid, title, "cancelled"))
            continue

        raw_start = _decoded(component, "DTSTART")
        if raw_start is None:
            result.skipped.append(SkippedItem(uid, title, "missing or unreadable start time"))
            continue

        all_day = _is_all_day(raw_start)
        raw_end = _decoded(component, "DTEND")
        duration = _decoded(component, "DURATION")

        if all_day:
            start = _day_start(raw_start)
            if raw_end is not None and _is_all_day(raw_end):
                end = _day_start(raw_end)
            elif isinstance(duration, timedelta):
                end = start + duration
            else:
                end = start + timedelta(days=1)
        else:
            start = _to_utc(raw_start, tz)
            if raw_end is not None and not _is_all_day(raw_end):
                end = _to_utc(raw_end, tz)
            elif isinstance(duration, timedelta):
                end = start + duration
            else:
                end = start  # RFC 5545: no end and no duration means zero length

        if end < start:
            result.skipped.append(SkippedItem(uid, title, "end is before start"))
            continue

        tzid = None
        if not all_day:
            tzid_param = getattr(component.get("DTSTART"), "params", {}).get("TZID")
            if tzid_param:
                tzid = str(tzid_param)
            elif raw_start.tzinfo is not None:
                tzid = "UTC"

        rrule_prop = component.get("RRULE")
        recurrence_id = _decoded(component, "RECURRENCE-ID")
        if recurrence_id is not None:
            recurrence_id = (
                _day_start(recurrence_id) if _is_all_day(recurrence_id) else _to_utc(recurrence_id, tz)
            )

        result.events.append(
            ParsedEvent(
                uid=uid or _fallback_uid(title, start),
                title=title,
                start=start,
                end=end,
                all_day=all_day,
                tzid=tzid,
                description=_text(component, "DESCRIPTION"),
                location=_text(component, "LOCATION"),
                rrule=rrule_prop.to_ical().decode() if rrule_prop is not None else None,
                exdates=_exdates(component, tz),
                recurrence_id=recurrence_id,
            )
        )

    return result
