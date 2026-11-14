from sqlmodel import SQLModel


class ImportIssue(SQLModel):
    uid: str | None
    title: str | None
    reason: str


class ImportResult(SQLModel):
    created: int
    duplicates: int  # already in the calendar, so not added again
    event_ids: list[int]
    skipped: list[ImportIssue]  # left out on purpose (cancelled, unsupported, ...)
    failed: list[ImportIssue]  # the events API rejected these
    warnings: list[ImportIssue]  # imported, but something was approximated
