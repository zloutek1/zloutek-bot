import logging

import discord
from discord.ext import commands

from bot.core.adapters.discord.utils import ReactionEventHydrator
from bot.starboard.adapters.discord.mappers import MessageMapper, ReactionMapper
from bot.starboard.application.services import StarboardService

log = logging.getLogger(__name__)


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
