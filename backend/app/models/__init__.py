# Import every table model here. SQLModel.metadata.create_all() (in init_db) only
# creates tables for models that have been imported, so a model missing from this
# file silently never gets a table.

from app.models.calendar import Calendar, CalendarShare
from app.models.user import User

__all__ = ["Calendar", "CalendarShare", "User"]
