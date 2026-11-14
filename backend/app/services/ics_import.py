from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from icalendar.timezone.windows_to_olson import WINDOWS_TO_OLSON

from app.schemas.event import EventCreate, Visibility
from app.services.ics_parser import ParsedEvent

# the API rejects timed events where end <= start, but ICS allows events with no end
DEFAULT_DURATION = timedelta(hours=1)


@dataclass
class BuiltEvent:
    body: EventCreate
    warnings: list[str] = field(default_factory=list)


def _valid_zone(name: str) -> str | None:
    try:
        ZoneInfo(name)
        return name
    except Exception:
        return None


def resolve_timezone(tzid: str | None, default_tz: str) -> tuple[str, str | None]:
    """Pick an IANA timezone name. Returns (name, warning or None)."""
    if tzid is None:
        return default_tz, None
    if _valid_zone(tzid):
        return tzid, None
    mapped = WINDOWS_TO_OLSON.get(tzid)  # outlook uses names like "Eastern Standard Time"
    if mapped and _valid_zone(mapped):
        return mapped, None
    return default_tz, f"unknown timezone {tzid!r}, used {default_tz} instead"


def normalize_rrule(rule: str, tz: str) -> str:
    """Make an ICS RRULE safe for recurrence.py.

    Google and Apple write UNTIL in utc ("20261231T045959Z"). recurrence.py parses
    rules against a naive local dtstart, and dateutil errors on that combination,
    so convert UNTIL into the event's local time (no Z).
    """
    parts = []
    for part in rule.strip().removeprefix("RRULE:").split(";"):
        key, _, value = part.partition("=")
        if key.upper() == "UNTIL" and value.upper().endswith("Z"):
            utc = datetime.strptime(value[:-1], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            local = utc.astimezone(ZoneInfo(tz)).replace(tzinfo=None)
            part = "UNTIL=" + local.strftime("%Y%m%dT%H%M%S")
        parts.append(part)
    return ";".join(parts)


def build_event_create(pe: ParsedEvent, default_tz: str, visibility: Visibility = "private") -> BuiltEvent:
    warnings: list[str] = []

    if pe.all_day:
        tz = default_tz
        # naive midnight dates; the end is already exclusive, which is what the API expects
        start = pe.start.replace(tzinfo=None)
        end = pe.end.replace(tzinfo=None)
    else:
        if pe.tzid == "UTC" and pe.rrule is None:
            # one-off utc event: show it in the calendar's own timezone
            tz = default_tz
        elif pe.tzid == "UTC":
            # a utc recurring event really does repeat at a fixed utc time, keep that
            tz = "UTC"
        else:
            tz, warning = resolve_timezone(pe.tzid, default_tz)
            if warning:
                warnings.append(warning)
        start, end = pe.start, pe.end
        if end <= start:
            end = start + DEFAULT_DURATION
            warnings.append("no end time in the file, defaulted to 1 hour")

    rrule = None
    if pe.rrule:
        rrule = normalize_rrule(pe.rrule, tz)
        if pe.exdates:
            warnings.append(
                f"{len(pe.exdates)} excluded date(s) can't be stored yet, "
                "those occurrences will still show up"
            )

    body = EventCreate(
        title=pe.title,
        description=pe.description,
        location=pe.location,
        all_day=pe.all_day,
        start=start,
        end=end,
        timezone=tz,
        visibility=visibility,
        rrule=rrule,
    )
    return BuiltEvent(body=body, warnings=warnings)
