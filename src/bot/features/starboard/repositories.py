from datetime import datetime
from typing import Protocol

from .models import StarboardMessage


class StarboardRepository(Protocol):
    async def save_starboard_message(self, message: StarboardMessage) -> None:
        ...

    async def get_starboard_message(self, original_message_id: int) -> StarboardMessage | None:
        ...

    async def update_reaction_count(self, message_id: int, reaction_count: int) -> None:
        ...

    async def get_pending_updates(self, cutoff_time: datetime) -> list[StarboardMessage]:
        ...
