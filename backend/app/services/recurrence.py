# helper stuff for repeating events and timezones

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil.rrule import rrulestr

ALLOWED_FREQS = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}


def get_zone(tz: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"Unknown timezone: {tz}")


def to_local(dt: datetime, tz: str) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(get_zone(tz)).replace(tzinfo=None)


def localize(naive: datetime, tz: str) -> datetime:
    return naive.replace(tzinfo=get_zone(tz))


def check_rrule(rule: str) -> str:
    rule = rule.strip().removeprefix("RRULE:")
    freq = next((p.split("=", 1)[1] for p in rule.split(";") if p.upper().startswith("FREQ=")), "")
    if freq.upper() not in ALLOWED_FREQS:
        raise ValueError(f"FREQ must be one of {sorted(ALLOWED_FREQS)}")
    try:
        rrulestr(rule, dtstart=datetime(2000, 1, 1))
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid rrule: {e}")
    return rule


def expand(
    start_local: datetime,
    end_local: datetime,
    tz: str,
    rule: str | None,
    window_start: datetime,
    window_end: datetime,
) -> list[tuple[datetime, datetime]]:
    length = end_local - start_local

    def overlaps(s, e):
        return s < window_end and e > window_start

    if rule is None:
        s, e = localize(start_local, tz), localize(end_local, tz)
        return [(s, e)] if overlaps(s, e) else []

    # do it in local time so dst doesnt mess up the hour
    lo = to_local(window_start, tz) - length - timedelta(days=1)
    hi = to_local(window_end, tz) + timedelta(days=1)
    out = []
    for occ in rrulestr(rule, dtstart=start_local).between(lo, hi, inc=True):
        s, e = localize(occ, tz), localize(occ + length, tz)
        if overlaps(s, e):
            out.append((s, e))
    return out
