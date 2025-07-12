import logging
from typing import NamedTuple

import discord
from bot.core.database import async_session_factory as session_factory
from bot.adapters.database.starboard import OrmStarboardRepository, StarboardMapper
from bot.adapters.discord.utils import DiscordEntityFetcher
from bot.features.starboard.models import MessageData, ReactionData, StarboardEntry
from bot.features.starboard.services import STARBOARD_CHANNEL_ID, StarboardService
from discord.ext import commands

log = logging.getLogger(__name__)


class FetchedEntities(NamedTuple):
    """A data class to hold the fetched entities for type-safe access."""

    guild: discord.Guild
    author: discord.Member | discord.User  # The author of the original message
    reacter: discord.Member | discord.User  # The user who added the reaction
    channel: discord.abc.Messageable
    message: discord.Message
    reaction: discord.Reaction


class StarboardEmbed(discord.Embed):
    """A custom embed class for starboard messages."""

    def __init__(self, entry: StarboardEntry, author: discord.Member | discord.User):
        super().__init__(color=discord.Color.gold(), timestamp=entry.created_at)

        self.set_author(name=author.display_name, icon_url=author.display_avatar.url)

        self.description = entry.content

        self.add_field(name="Original Message", value=f"[Jump to Message]({entry.original_jump_url})", inline=False)

        self.add_field(name="Stars", value=f"⭐ {entry.reaction_count}", inline=True)

        if entry.attachment_urls:
            self.set_image(url=entry.attachment_urls[0])


class StarboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot, service: StarboardService) -> None:
        self.bot = bot
        self.fetcher = DiscordEntityFetcher(bot)
        self.service = service

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if not self._is_valid_reaction_event(payload):
            return

        entities = await self._fetch_discord_entities(payload)
        if not entities:
            log.warning(f"Failed to fetch all required entities for payload: {payload}")
            return

        starboard_channel = await self.fetcher.fetch_messageable_channel(STARBOARD_CHANNEL_ID)
        if not isinstance(starboard_channel, discord.TextChannel):
            log.error(f"Could not find starboard channel with ID {STARBOARD_CHANNEL_ID}")
            return

        message_data = self._convert_to_message_data(entities.message)
        reaction_data = self._convert_to_reaction_data(entities.reaction, entities.message.id)

        entry = await self.service.process_reaction_add(message_data, reaction_data)
        if not entry:
            return

        embed = StarboardEmbed(entry, author=entities.author)
        if entry.starboard_message_id:
            try:
                starboard_message = await starboard_channel.fetch_message(entry.starboard_message_id)
                await starboard_message.edit(embed=embed)
                log.info(f"Updated starboard message {starboard_message.id}")
                return
            except discord.NotFound:
                pass

        # This is a new entry, so we send a new message
        starboard_message = await starboard_channel.send(embed=embed)
        log.info(f"Created new starboard message {starboard_message.id}")
        # Now, we tell the service the ID of the message we just created

        await self.service.set_starboard_message_id(
            original_message_id=entry.original_message_id, starboard_message_id=starboard_message.id
        )

    def _is_valid_reaction_event(self, payload: discord.RawReactionActionEvent) -> bool:
        # Ignore DMs
        if payload.guild_id is None:
            return False

        # Ignore bots
        if payload.member and payload.member.bot:
            return False

        # Prevent starring a message in the starboard channel itself
        # if payload.channel_id == STARBOARD_CHANNEL_ID:
        #    return False

        return True

    async def _fetch_discord_entities(self, payload: discord.RawReactionActionEvent) -> FetchedEntities | None:
        if not (guild := await self.fetcher.fetch_guild(payload.guild_id)):
            return None

        if not (member := await self.fetcher.fetch_member(guild, payload.user_id)):
            return None

        if not (channel := await self.fetcher.fetch_messageable_channel(payload.channel_id)):
            return None

        if not (message := await self.fetcher.fetch_message(channel, payload.message_id)):
            return None

        if not (reaction := await self.fetcher.fetch_reaction(message, payload.emoji)):
            return None

        return FetchedEntities(guild, message.author, member, channel, message, reaction)

    def _convert_to_message_data(self, message: discord.Message) -> MessageData:
        """Convert a Discord message to the MessageData DTO."""
        assert message.guild
        return MessageData(
            id=message.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id,
            author_id=message.author.id,
            content=message.content,
            attachment_urls=[att.url for att in message.attachments],
            jump_url=message.jump_url,
            created_at=message.created_at,
        )

    def _convert_to_reaction_data(self, reaction: discord.Reaction, message_id: int) -> ReactionData:
        """Convert a Discord reaction to domain ReactionData."""
        return ReactionData(emoji=str(reaction.emoji), count=reaction.count, message_id=message_id)


async def setup(bot: commands.Bot) -> None:
    repository = OrmStarboardRepository(session_factory, StarboardMapper())
    service = StarboardService(repository)
    cog = StarboardCog(bot=bot, service=service)
    await bot.add_cog(cog)
