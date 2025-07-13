import logging

import discord
from discord.ext import commands

from bot.core.adapters.discord.utils import ReactionEventHydrator
from bot.core.typing import Mapper
from bot.starboard.application.ports import StarboardMessage, StarboardReaction
from bot.starboard.application.services import StarboardService

log = logging.getLogger(__name__)


class MessageMapper(Mapper[StarboardMessage, discord.Message]):
    def from_model(self, model: StarboardMessage) -> discord.Message:
        raise NotImplementedError()

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


class ReactionMapper(Mapper[StarboardReaction, discord.Reaction]):
    def from_model(self, model: StarboardReaction) -> discord.Reaction:
        raise NotImplementedError()

    def to_model(self, entity: discord.Reaction) -> StarboardReaction:
        return StarboardReaction(emoji=str(entity.emoji), count=entity.count, message_id=entity.message.id)


class StarboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot, service: StarboardService) -> None:
        self.bot = bot
        self.service = service
        self.hydrator = ReactionEventHydrator(bot)
        self.message_mapper = MessageMapper()
        self.reaction_mapper = ReactionMapper()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if not self._is_relevant_reaction_event(payload):
            return

        entities = await self.hydrator.hydrate(payload)
        if not entities:
            log.error(f"Failed to fetch entities for reaction event: {payload}")
            return

        message = self.message_mapper.to_model(entities.reaction.message)
        reaction = self.reaction_mapper.to_model(entities.reaction)

        await self.service.handle_reaction_added(message, reaction)

    def _is_relevant_reaction_event(self, payload: discord.RawReactionActionEvent) -> bool:
        # Ignore DMs
        if payload.guild_id is None:
            return False

        # Ignore bots
        if payload.member and payload.member.bot:
            return False

        return True
