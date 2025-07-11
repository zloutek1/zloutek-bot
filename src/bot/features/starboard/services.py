import logging
from datetime import UTC, datetime

from bot.features.starboard.models import MessageData, MessageReference, ReactionData, StarboardMessage

from .repositories import StarboardRepository

log = logging.getLogger(__name__)


class StarboardService:
    def __init__(self, repository: StarboardRepository):
        self._repository = repository

    async def process_reaction_add(self, message: MessageData, reaction: ReactionData) -> StarboardMessage | None:
        log.info(f"Processing reaction add for message {message.id} with reaction {reaction.emoji}")

        if not self._should_create_starboard_entry(message, reaction):
            log.debug("Reaction does not meet criteria for starboard entry")
            return None

        existing = await self._repository.get_starboard_message(message.id)
        if existing:
            log.debug(f"Updating existing starboard entry for message {message.id}")
            await self._repository.update_reaction_count(message.id, reaction.count)
            return existing

        log.debug(f"Creating new starboard entry for message {message.id}")
        entry = self._create_starboard_entry(message, reaction)
        await self._repository.save_starboard_message(entry)
        return entry

    def _should_create_starboard_entry(self, message_data: MessageData, reaction_data: ReactionData) -> bool:
        """Check if a reaction meets the criteria for starboard inclusion."""

        return (
            reaction_data.emoji == "⭐"  # Only star reactions
            and reaction_data.count >= 1
        )

    def _create_starboard_entry(self, message_data: MessageData, reaction_data: ReactionData) -> StarboardMessage:
        """Create a new starboard entry from message and reaction data."""
        now = datetime.now(UTC)

        return StarboardMessage(
            original=MessageReference(
                guild_id=message_data.guild_id,
                channel_id=message_data.channel_id,
                message_id=message_data.id,
            ),
            starboard=MessageReference(
                guild_id=message_data.guild_id,
                channel_id=message_data.channel_id,
                message_id=None,  # will be filled later
            ),
            reaction_count=reaction_data.count,
            last_updated=now,
        )

    async def save_starred_message(self, original_message_id: int, starboard_message_id: int) -> None:
        """Mark a message as starred in the database."""
        await self._repository.set_starboard_message(original_message_id, starboard_message_id)
