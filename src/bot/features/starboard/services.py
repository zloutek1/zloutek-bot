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

        entry = await self._repository.find(message.id)
        if entry:
            entry.reaction_count = reaction.count
            entry.updated_at = datetime.now(UTC)
            entry.content = message.content
            entry.attachment_urls = message.attachment_urls

            await self._repository.update(entry)
            return entry

        log.info(f"Creating new starboard entry for message {message.id}")
        entry = self._create_starboard_entry(message, reaction)
        await self._repository.create(entry)
        return entry

    def _meets_starboard_criteria(self, message_data: MessageData, reaction_data: ReactionData) -> bool:
        """Check if a reaction meets the criteria for starboard inclusion."""

        return (
            reaction_data.emoji == "⭐"  # Only star reactions
            and reaction_data.count >= STARBOARD_THRESHOLD
        )

    def _create_starboard_entry(self, message_data: MessageData, reaction_data: ReactionData) -> StarboardEntry:
        """Creates a new StarboardEntry domain model."""
        now = datetime.now(UTC)
        return StarboardEntry(
            original_message_id=message_data.id,
            original_channel_id=message_data.channel_id,
            original_guild_id=message_data.guild_id,
            original_author_id=message_data.author_id,
            original_jump_url=message_data.jump_url,
            starboard_channel_id=STARBOARD_CHANNEL_ID,  # From config
            content=message_data.content,
            attachment_urls=message_data.attachment_urls,
            reaction_count=reaction_data.count,
            created_at=now,
            updated_at=now,
        )

    async def set_starboard_message_id(self, original_message_id: int, starboard_message_id: int) -> None:
        """Mark a message as starred in the database."""
        entry = await self._repository.find(original_message_id)
        if not entry:
            return

        entry.starboard_message_id = starboard_message_id
        await self._repository.update(entry)
