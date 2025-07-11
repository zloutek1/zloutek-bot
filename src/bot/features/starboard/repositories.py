from typing import Protocol

from .models import StarboardMessage


class StarboardRepository(Protocol):
    async def save_starboard_message(self, message: StarboardMessage) -> None: ...
    async def get_starboard_message(
        self, original_message_id: int
    ) -> StarboardMessage | None: ...
