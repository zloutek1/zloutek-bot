from datetime import datetime

from pydantic import BaseModel


class MessageData(BaseModel):
    id: int
    channel_id: int
    guild_id: int
    author_id: int
    content: str
    attachment_urls: list[str]
    created_at: datetime


class ReactionData(BaseModel):
    emoji: str
    count: int
    message_id: int


class MessageReference(BaseModel):
    guild_id: int
    channel_id: int
    message_id: int | None


class StarboardMessage(BaseModel):
    original: MessageReference
    starboard: MessageReference | None

    reaction_count: int
    last_updated: datetime
