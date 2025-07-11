import logging
from typing import NamedTuple

import discord
from bot.adapters.database.database import async_session_factory as session_factory
from bot.adapters.database.starboard import OrmStarboardRepository
from bot.adapters.discord.utils import DiscordEntityFetcher
from bot.features.starboard.models import MessageData, ReactionData
from bot.features.starboard.services import StarboardService
from discord.ext import commands

log = logging.getLogger(__name__)


class FetchedEntities(NamedTuple):
    """A data class to hold the fetched entities for type-safe access."""

    guild: discord.Guild
    member: discord.Member
    channel: discord.abc.Messageable
    message: discord.Message
    reaction: discord.Reaction


class StarboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot, service: StarboardService) -> None:
        self.bot = bot
        self.service = service

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        log.info(f"Received reaction add event: {payload}")
        if not self._is_valid_reaction_event(payload):
            log.debug("Ignoring invalid reaction add event")
            return

        fetcher = DiscordEntityFetcher(self.bot)
        entities = await self._fetch_discord_entities(fetcher, payload)
        if not entities:
            log.debug("Failed to fetch required entities")
            return

        message_data = self._convert_to_message_data(entities.message)
        reaction_data = self._convert_to_reaction_data(entities.reaction, entities.message.id)

        starboard_message_data = await self.service.process_reaction_add(message_data, reaction_data)
        if not starboard_message_data:
            log.debug("No starboard entry created")
            return

        print("starred message data", starboard_message_data)
        channel = await fetcher.fetch_messageable_channel(payload.channel_id)
        if channel:
            starboard_message = await channel.send("[STARRED]" + starboard_message_data.model_dump_json())

        self.service.save_starred_message(entities.message.id, starboard_message.id)

    def _is_valid_reaction_event(self, payload: discord.RawReactionActionEvent) -> bool:
        # Ignore DMs
        if payload.guild_id is None:
            return False

        # Ignore bots
        if payload.member and payload.member.bot:
            return False

        return True

    async def _fetch_discord_entities(
        self, fetcher: DiscordEntityFetcher, payload: discord.RawReactionActionEvent
    ) -> FetchedEntities | None:
        if not (guild := await fetcher.fetch_guild(payload.guild_id)):
            return None

        if not (member := await fetcher.fetch_member(guild, payload.user_id)):
            return None

        if not (channel := await fetcher.fetch_messageable_channel(payload.channel_id)):
            return None

        if not (message := await fetcher.fetch_message(channel, payload.message_id)):
            return None

        if not (reaction := await fetcher.fetch_reaction(message, payload.emoji)):
            return None

        return FetchedEntities(guild, member, channel, message, reaction)

    def _convert_to_message_data(self, message: discord.Message) -> MessageData:
        """Convert a Discord message to domain MessageData."""
        attachment_urls = [attachment.url for attachment in message.attachments]

        assert message.guild
        return MessageData(
            id=message.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
            author_id=message.author.id,
            content=message.content,
            attachment_urls=attachment_urls,
            created_at=message.created_at,
        )

    def _convert_to_reaction_data(self, reaction: discord.Reaction, message_id: int) -> ReactionData:
        """Convert a Discord reaction to domain ReactionData."""
        return ReactionData(emoji=str(reaction.emoji), count=reaction.count, message_id=message_id)


async def setup(bot: commands.Bot) -> None:
    repository = OrmStarboardRepository(session_factory)
    service = StarboardService(repository)
    cog = StarboardCog(bot=bot, service=service)
    await bot.add_cog(cog)
