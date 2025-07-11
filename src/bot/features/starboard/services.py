from datetime import UTC, datetime

from bot.features.starboard.models import MessageData, ReactionData, StarboardMessage

from .repositories import StarboardRepository


class StarboardService:
    def __init__(self, repository: StarboardRepository):
        self._repository = repository

    async def process_reaction_add(self, message: MessageData, reaction: ReactionData) -> StarboardMessage | None:
        if not self._should_create_starboard_entry(message, reaction):
            return None

        existing = await self._repository.get_starboard_message(message.id)
        if existing:
            await self._repository.update_reaction_count(message.id, reaction.count)
            return existing

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
            original_message_id=message_data.id,
            original_channel_id=message_data.channel_id,
            starboard_message_id=None,  # Will be set when actually posted to starboard
            starboard_channel_id=0,  # Configure this based on your guild settings
            author_id=message_data.author_id,
            content=message_data.content,
            attachment_urls=message_data.attachment_urls,
            reaction_count=reaction_data.count,
            emoji_used=reaction_data.emoji,
            created_at=now,
            last_updated=now,
        )
