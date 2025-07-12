from datetime import datetime
from typing import Protocol

from .models import StarboardEntry


class StarboardRepository(Protocol):
    async def find(self, original_message_id: int) -> StarboardEntry | None: ...

    async def create(self, message: StarboardEntry) -> None: ...

    async def update(self, message: StarboardEntry) -> None: ...

    async def get_pending_updates(self, cutoff_time: datetime) -> list[StarboardEntry]: ...
