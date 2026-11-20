import uuid

from datetime import datetime, timezone

#IF SOMEONE IS SEEING THIS 😳

from sqlalchemy import CheckConstraint,Column,DateTime,UniqueConstraint

from sqlmodel import Field,SQLModel

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
LEVEL_PROFESSIONAL = "professional"
LEVEL_CLOSE = "close"

class Friendship(SQLModel , table = True):
    __tablename__= "friendships"
    __table_args__ = (
        UniqueConstraint("sender_id" , "reciever_id" , name = "uq_friendship_pair"),
        # has to be one SQL string. `"a" != "b"` is compared by python first and becomes CHECK (true)
        CheckConstraint("sender_id <> reciever_id" , name = "ck_friendship_not_self"),
    )

    id:int | None = Field(default = None , primary_key = True)
    sender_id: uuid.UUID = Field(foreign_key="profiles.id")
    reciever_id: uuid.UUID = Field(foreign_key="profiles.id" , index=True)
    status:str = Field(default=STATUS_PENDING , max_length=20)
    level:str = Field(default=LEVEL_PROFESSIONAL, max_length=20)
    created_at:datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column = Column(DateTime(timezone=True), nullable=False),
        )
