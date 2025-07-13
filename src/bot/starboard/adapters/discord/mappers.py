import discord

from bot.core.typing import ToModelMapper
from bot.starboard.application.ports import StarboardMessage, StarboardReaction


class MessageMapper(ToModelMapper[StarboardMessage, discord.Message]):
    def to_model(self, entity: discord.Message) -> StarboardMessage:
        if not entity.guild:
            raise ValueError("Message must be in a guild")

        return StarboardMessage(
            id=entity.id,
            channel_id=entity.channel.id,
            guild_id=entity.guild.id,
            author_id=entity.author.id,
            author_display_name=entity.author.display_name,
            author_avatar_url=entity.author.avatar.url if entity.author.avatar else None,
            content=entity.content,
            attachment_urls=[att.url for att in entity.attachments],
            jump_url=entity.jump_url,
            created_at=entity.created_at,
        )


class ReactionMapper(ToModelMapper[StarboardReaction, discord.Reaction]):
    def to_model(self, entity: discord.Reaction) -> StarboardReaction:
        return StarboardReaction(emoji=str(entity.emoji), count=entity.count, message_id=entity.message.id)
