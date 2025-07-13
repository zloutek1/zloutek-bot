from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from bot.core.typing import Id, Url
from bot.starboard.domain.models import StarboardEntry


class StarboardMessage(BaseModel):
    """
    Pure domain model representing a message that can be starred.
    This contains only the business data needed for starboard logic.
    """

    id: Id
    channel_id: Id
    guild_id: Id
    author_id: Id
    author_display_name: str
    author_avatar_url: Url
    content: str
    attachment_urls: list[Url]
    jump_url: Url
    created_at: datetime


class StarboardReaction(BaseModel):
    """
    Pure domain model representing a reaction on a message.
    Contains only the business data needed for starboard decisions.
    """

    emoji: str
    count: int
    message_id: Id


class StarboardRepository(Protocol):
    async def find_by_message_id(self, message_id: Id) -> StarboardEntry | None: ...

    async def save(self, entry: StarboardEntry) -> None: ...


class StarboardPresentation(BaseModel):
    author_display_name: str
    author_avatar_url: Url
    message_content: str
    reactions_display: str
    jump_url: Url
    channel_mention: str
    color: str  # Hex color code
    timestamp: datetime
    image_url: Url | None = None


class StarboardPresenter(Protocol):
    async def create_presentation(
        self, message: StarboardMessage, reaction: StarboardReaction, entry: StarboardEntry
    ) -> StarboardPresentation:
        """Create presentation data for a starboard message."""
        ...


class StarboardPublisher(Protocol):
    async def post_starboard_message(self, entry: StarboardEntry, presentation: StarboardPresentation) -> Id:
        """Post a starboard message and return the message ID."""
        ...

    async def update_starboard_message(self, entry: StarboardEntry, presentation: StarboardPresentation) -> None:
        """Update an existing starboard message."""
        ...
