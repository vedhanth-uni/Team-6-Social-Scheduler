import uuid

from sqlmodel import Field, SQLModel


# the email from someone's login, kept off profiles so it never shows up in search results
class ProfileEmail(SQLModel, table=True):
    __tablename__ = "profile_emails"

    profile_id: uuid.UUID = Field(foreign_key="profiles.id", primary_key=True)
    email: str = Field(max_length=320, index=True)
