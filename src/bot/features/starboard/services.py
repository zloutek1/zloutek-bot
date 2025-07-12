import logging
from datetime import UTC, datetime

from bot.features.starboard.models import MessageData, ReactionData, StarboardEntry

from .repositories import StarboardRepository

log = logging.getLogger(__name__)


STARBOARD_CHANNEL_ID = 1393196186164264980  # Example Starboard Channel ID
STARBOARD_THRESHOLD = 1  # Example: 3 stars needed


class StarboardService:
    def __init__(self, repository: StarboardRepository):
        self._repository = repository

    async def process_reaction_add(self, message: MessageData, reaction: ReactionData) -> StarboardEntry | None:
        """Send a message to a starboard channel if the reaction meets criteria."""

        if not self._meets_starboard_criteria(message, reaction):
            log.debug(f"Reaction {reaction.emoji} does not meet criteria.")
            return None

        old_entry = await self._repository.find(message.id)
        if old_entry:
            entry = old_entry.to_update(message, reaction)
            await self._repository.update(entry)
            return entry
        else:
            log.info(f"Creating new starboard entry for message {message.id}")
            entry = StarboardEntry.to_create(message, reaction, STARBOARD_CHANNEL_ID)
            await self._repository.create(entry)
            return entry

    def _meets_starboard_criteria(self, message_data: MessageData, reaction_data: ReactionData) -> bool:
        """Check if a reaction meets the criteria for starboard inclusion."""

        return (
            reaction_data.emoji == "⭐"  # Only star reactions
            and reaction_data.count >= STARBOARD_THRESHOLD
        )

    async def set_starboard_message_id(self, original_message_id: int, starboard_message_id: int) -> None:
        """Mark a message as starred in the database."""
        entry = await self._repository.find(original_message_id)
        if not entry:
            return

        entry = entry.with_starboard_message_id(starboard_message_id)

        await self._repository.update(entry)
