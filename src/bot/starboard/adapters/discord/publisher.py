import logging

import discord
from discord.ext import commands

from bot.core.adapters.discord.errors import EntityNotFoundError
from bot.core.typing import Id
from bot.starboard.application.ports import StarboardPresentation
from bot.starboard.domain.models import StarboardEntry

log = logging.getLogger(__name__)


class StarboardEmbed(discord.Embed):
    def __init__(self, presentation: StarboardPresentation) -> None:
        super().__init__(color=int(presentation.color.lstrip("#"), 16), timestamp=presentation.timestamp)

        self.set_author(name=presentation.author_display_name, icon_url=presentation.author_avatar_url)

        self.description = f"""
            {presentation.message_content}

            {presentation.reactions_display}
            [Jump to message]({presentation.jump_url}) in {presentation.channel_mention}
        """

        if presentation.image_url:
            self.set_image(url=presentation.image_url)


class DiscordStarboardPublisher:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def post_starboard_message(self, entry: StarboardEntry, presentation: StarboardPresentation) -> Id:
        """
        Post a new starboard message to Discord and return the message ID.
        """

        channel = self._get_cached_channel(entry.starboard_channel_id)

        embed = StarboardEmbed(presentation)
        message = await channel.send(embed=embed)

        log.info(f"Posted starboard message {message.id} for original message {entry.original_message_id}")
        return message.id

    async def update_starboard_message(self, entry: StarboardEntry, presentation: StarboardPresentation) -> None:
        """
        Update an existing starboard message in Discord.
        """
        if not entry.starboard_message_id:
            log.warning(
                f"Cannot update starboard message for entry {entry.original_message_id}: no starboard message ID"
            )
            return

        channel = self._get_cached_channel(entry.starboard_channel_id)
        message = await channel.fetch_message(entry.starboard_message_id)

        embed = StarboardEmbed(presentation)
        await message.edit(embed=embed)

        log.info(
            f"Updated starboard message {entry.starboard_message_id} for original message {entry.original_message_id}"
        )

    def _get_cached_channel(self, channel_id: int) -> discord.abc.Messageable:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            raise EntityNotFoundError(f"Channel with ID {channel_id} not found")

        if not isinstance(channel, discord.abc.Messageable):
            raise ValueError(f"Channel with ID {channel_id} is not a messageable channel")

        return channel
