# Importing a model here registers its table with SQLModel.metadata,
# which is what create_all() uses. Add every new model to this list.

from app.models.profile import Profile
from app.models.friendships import Friendship
from app.models.profile_email import ProfileEmail
from app.models.calendar import Calendar, CalendarShare
from app.models.event import Event, Attendee