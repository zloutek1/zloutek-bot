from bot.starboard.application.ports import StarboardMessage, StarboardPresentation, StarboardReaction
from bot.starboard.domain.models import StarboardEntry


class DiscordStarboardPresenter:
    async def create_presentation(
        self, message: StarboardMessage, reaction: StarboardReaction, entry: StarboardEntry
    ) -> StarboardPresentation:
        return StarboardPresentation(
            author_display_name=message.author_display_name,
            author_avatar_url=message.author_avatar_url,
            message_content=message.content,
            reactions_display=f"{reaction.count} {reaction.emoji}",
            color="#FFD700",  # Gold color
            timestamp=message.created_at,
            jump_url=message.jump_url,
            channel_mention=f"<#{message.channel_id}>",
            image_url=message.attachment_urls[0] if message.attachment_urls else None,
        )
