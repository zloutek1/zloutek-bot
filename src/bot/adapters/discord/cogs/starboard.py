from typing import NamedTuple

import discord
from bot.adapters.database.database import async_session_factory as session_factory
from bot.adapters.database.starboard import StarboardRepository
from bot.adapters.discord.utils import DiscordEntityFetcher
from bot.features.starboard.models import MessageData, ReactionData
from bot.features.starboard.services import StarboardService
from discord.ext import commands


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
        if not self._is_valid_reaction_event(payload):
            return

        entities = await self._fetch_discord_entities(payload)
        if not entities:
            return

        message_data = self._convert_to_message_data(entities.message)
        reaction_data = self._convert_to_reaction_data(entities.reaction, entities.message.id)

        await self.service.process_reaction_add(message_data, reaction_data)

    def _is_valid_reaction_event(self, payload: discord.RawReactionActionEvent) -> bool:
        # Ignore DMs
        if payload.guild_id is None:
            return False

        # Ignore bots
        if payload.member and payload.member.bot:
            return False

        return True

    async def _fetch_discord_entities(self, payload: discord.RawReactionActionEvent) -> FetchedEntities | None:
        fetcher = DiscordEntityFetcher(self.bot)

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
    repository = StarboardRepository(session_factory)
    service = StarboardService(repository)
    cog = StarboardCog(bot=bot, service=service)
    await bot.add_cog(cog)
