from datetime import datetime

from pydantic import BaseModel, Field

from bot.core.typing import Id, Url

# ==========================================
# --- Input DTOs (Data Transfer Objects) ---
# ==========================================


class MessageData(BaseModel):
    """Holds information about a Discord message."""

    id: Id
    channel_id: Id
    guild_id: Id
    author_id: Id
    content: str
    attachment_urls: list[Url]
    jump_url: Url
    created_at: datetime


class ReactionData(BaseModel):
    """Holds information about a Discord reaction."""

    emoji: str
    count: int
    message_id: Id


# ====================
# --- Domain Model ---
# ====================


class StarboardEntry(BaseModel):
    """
    Represents a single, complete entry on the starboard. This is the
    canonical domain model.
    """

    # --- Original Message Info ---
    original_message_id: Id
    original_channel_id: Id
    original_guild_id: Id
    original_author_id: Id
    original_jump_url: Url

    # --- Starboard Message Info ---
    starboard_message_id: Id | None = None  # Populated after the starboard message is sent
    starboard_channel_id: Id  # The ID of the channel where star messages go

    # --- Content and State ---
    content: str
    attachment_urls: list[Url] = Field(default_factory=list)
    reaction_count: int

    # --- Timestamps ---
    created_at: datetime
    updated_at: datetime
