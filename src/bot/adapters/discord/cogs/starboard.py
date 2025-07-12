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
    reacter: discord.Member | discord.User
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

        entities = await self.fetcher.fetch_reaction_action_event(payload)
        if not entities:
            log.error(f"Failed to fetch all required entities for payload: {payload}")
            return

        await self.on_reaction_add(entities.reaction, entities.user)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User | discord.Member) -> None:
        log.debug(f"Processing reaction add for message {reaction.message.id} by user {user.id}")

        message_data = self._convert_to_message_data(reaction.message)
        reaction_data = self._convert_to_reaction_data(reaction, reaction.message.id)

        entry = await self.service.process_reaction_add(message_data, reaction_data)
        if not entry:
            return

        await self._update_or_create_starboard_message(entry, reaction.message.author)

    async def _update_or_create_starboard_message(
        self, entry: StarboardEntry, author: discord.Member | discord.User
    ) -> None:
        """Updates an existing starboard message or creates a new one."""

        starboard_channel = await self._get_starboard_channel()
        if not isinstance(starboard_channel, discord.TextChannel):
            log.critical(f"Starboard channel with ID {STARBOARD_CHANNEL_ID} is not a text channel.")
            return

        embed = StarboardEmbed(entry, author=author)

        if entry.starboard_message_id:
            await self._update_starboard_message(starboard_channel, entry, embed)
            return

        await self._create_starboard_message(starboard_channel, entry, embed)

    async def _get_starboard_channel(self) -> discord.abc.Messageable | None:
        """Fetches the starboard channel."""
        channel = await self.fetcher.fetch_messageable_channel(STARBOARD_CHANNEL_ID)
        if not channel:
            log.error(f"Could not find starboard channel with ID {STARBOARD_CHANNEL_ID}")
        return channel

    async def _create_starboard_message(
        self, starboard_channel: discord.TextChannel, entry: StarboardEntry, embed: discord.Embed
    ) -> None:
        """Creates a new message in the starboard channel."""
        starboard_message = await starboard_channel.send(embed=embed)
        log.info(f"Created new starboard message {starboard_message.id}")
        # Now, we tell the service the ID of the message we just created

        await self.service.set_starboard_message_id(
            original_message_id=entry.original_message_id, starboard_message_id=starboard_message.id
        )

    async def _update_starboard_message(
        self, starboard_channel: discord.TextChannel, entry: StarboardEntry, embed: discord.Embed
    ) -> None:
        """Updates an existing message in the starboard channel."""

        assert entry.starboard_message_id is not None

        try:
            starboard_message = await starboard_channel.fetch_message(entry.starboard_message_id)
            await starboard_message.edit(embed=embed)
            log.info(
                f"Updated starboard message {starboard_message.id} for original message {entry.original_message_id}"
            )
        except discord.NotFound:
            # If the starboard message was deleted, we should potentially clean up the entry
            log.warning(
                f"Starboard message {entry.starboard_message_id} not found. Original message: {entry.original_message_id}. Skipping update."
            )
            await self._create_starboard_message(starboard_channel, entry, embed)

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
