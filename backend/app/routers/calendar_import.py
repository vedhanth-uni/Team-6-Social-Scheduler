# POST /calendars/{cal_id}/import  -- upload an .ics file, get its events added to the calendar.
#
# This reuses the existing event code (create_event, resolve_times, validate_rrule) instead of
# writing to the database itself, so imported events go through the exact same validation and
# permission checks as events created by hand. Needs editor access on the calendar.
#
# Safe to re-run: events already in the calendar (same title, times and rule) are skipped.
# Each event is saved on its own, so one bad event doesn't stop the rest.

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.event import Event
from app.auth_profile import current_profile
from app.models.profile import Profile
from app.routers.calendars import load_calendar
from app.routers.events import create_event, resolve_times, validate_rrule
from app.schemas.event import Visibility
from app.schemas.ics_import import ImportIssue, ImportResult
from app.services.ics_import import build_event_create
from app.services.ics_parser import ICSParseError, parse_ics

router = APIRouter(tags=["Import"])

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_EVENTS = 2000


@router.post("/calendars/{cal_id}/import", response_model=ImportResult)
def import_ics(
    cal_id: int,
    file: UploadFile = File(description=".ics calendar file"),
    default_tz: str | None = Query(
        default=None,
        description="timezone for times with no timezone in the file (uses the calendar's if empty)",
    ),
    visibility: Visibility = Query(default="private", description="visibility given to every imported event"),
    skip_duplicates: bool = Query(default=True),
    user: Profile = Depends(current_profile),
    session: Session = Depends(get_session),
):
    cal, _ = load_calendar(cal_id, user, session, need="editor")

    data = file.file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File is too big (5 MB max)")

    tz = default_tz or cal.timezone
    try:
        parsed = parse_ics(data, default_tz=tz)
    except (ICSParseError, ValueError) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))
    if len(parsed.events) > MAX_EVENTS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Too many events ({len(parsed.events)}), the limit is {MAX_EVENTS} per import",
        )

    result = ImportResult(
        created=0,
        duplicates=0,
        event_ids=[],
        skipped=[ImportIssue(uid=s.uid, title=s.title, reason=s.reason) for s in parsed.skipped],
        failed=[],
        warnings=[],
    )

    existing = session.exec(
        select(Event).where(Event.calendar_id == cal.id, Event.deleted_at == None)  # noqa: E711
    ).all()
    seen = {(e.title, e.start_local, e.end_local, e.rrule) for e in existing}

    for pe in parsed.events:
        if pe.recurrence_id is not None:
            # one edited occurrence of a repeating event; events can't store exceptions yet
            result.skipped.append(ImportIssue(
                uid=pe.uid, title=pe.title,
                reason="edited single occurrence of a recurring event (not supported yet)",
            ))
            continue

        built = build_event_create(pe, tz, visibility)
        body = built.body
        try:
            # same helpers create_event uses, so the duplicate check compares what would be stored
            start_local, end_local = resolve_times(body.timezone, body.all_day, body.start, body.end)
            rule = validate_rrule(body.rrule)
            key = (body.title, start_local, end_local, rule)
            if skip_duplicates and key in seen:
                result.duplicates += 1
                continue
            created = create_event(cal.id, body, user, session)
        except HTTPException as e:
            session.rollback()
            result.failed.append(ImportIssue(uid=pe.uid, title=pe.title, reason=str(e.detail)))
            continue

        seen.add(key)
        result.created += 1
        result.event_ids.append(created.id)
        result.warnings += [ImportIssue(uid=pe.uid, title=pe.title, reason=w) for w in built.warnings]

    return result
