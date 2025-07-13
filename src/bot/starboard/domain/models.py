from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from bot.core.typing import Id


class StarboardStatus(Enum):
    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"


class StarboardEntry(BaseModel):
    """
    Domain model representing a complete starboard entry.
    This is the aggregate root for the starboard bounded context.
    """

    original_message_id: Id
    starboard_message_id: Id | None = None
    starboard_channel_id: Id
    status: StarboardStatus = StarboardStatus.PENDING
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    @classmethod
    def create(cls, original_message_id: Id, starboard_channel_id: Id) -> "StarboardEntry":
        return cls(
            original_message_id=original_message_id,
            starboard_channel_id=starboard_channel_id,
        )

    def mark_as_posted(self, starboard_message_id: int) -> "StarboardEntry":
        self.starboard_message_id = starboard_message_id
        self.status = StarboardStatus.POSTED
        self.updated_at = datetime.now()
        return self

    def update_timestamp(self) -> "StarboardEntry":
        self.updated_at = datetime.now()
        return self

    def assign_starboard_message(self, starboard_message_id: Id) -> "StarboardEntry":
        self.starboard_message_id = starboard_message_id
        self.updated_at = datetime.now()
        return self
