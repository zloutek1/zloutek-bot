import logging

import discord
from discord.ext import commands

from bot.core.adapters.discord.utils import ReactionEventHydrator
from bot.starboard.application.ports import StarboardMessage, StarboardReaction
from bot.starboard.application.services import StarboardService

log = logging.getLogger(__name__)


class StarboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot, service: StarboardService) -> None:
        self.bot = bot
        self.service = service
        self.hydrator = ReactionEventHydrator(bot)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if not self._is_relevant_reaction_event(payload):
            return

        # Fetch Discord entities
        entities = await self.hydrator.hydrate(payload)
        if not entities:
            log.error(f"Failed to fetch entities for reaction event: {payload}")
            return

        # Convert Discord objects to domain models
        message = self._convert_to_domain_message(entities.reaction.message)
        reaction = self._convert_to_domain_reaction(entities.reaction)

        await self.service.handle_reaction_added(message, reaction)

    def _is_relevant_reaction_event(self, payload: discord.RawReactionActionEvent) -> bool:
        # Ignore DMs
        if payload.guild_id is None:
            return False

        # Ignore bots
        if payload.member and payload.member.bot:
            return False

        return True

    def _convert_to_domain_message(self, discord_message: discord.Message) -> StarboardMessage:
        """
        Convert Discord message to domain model.
        This is the translation layer between Discord and domain.
        """
        assert discord_message.guild is not None
        return StarboardMessage(
            id=discord_message.id,
            channel_id=discord_message.channel.id,
            guild_id=discord_message.guild.id,
            author_id=discord_message.author.id,
            author_display_name=discord_message.author.display_name,
            author_avatar_url=discord_message.author.avatar.url,
            content=discord_message.content,
            attachment_urls=[att.url for att in discord_message.attachments],
            jump_url=discord_message.jump_url,
            created_at=discord_message.created_at,
        )

    def _convert_to_domain_reaction(self, discord_reaction: discord.Reaction) -> StarboardReaction:
        """
        Convert Discord reaction to domain model.
        This is the translation layer between Discord and domain.
        """
        return StarboardReaction(
            emoji=str(discord_reaction.emoji), count=discord_reaction.count, message_id=discord_reaction.message.id
        )
