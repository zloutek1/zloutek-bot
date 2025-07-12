from collections.abc import Awaitable, Callable
from typing import Any, NamedTuple

import discord
from discord.ext import commands


class ReactionActionEvent(NamedTuple):
    reaction: discord.Reaction
    user: discord.User | discord.Member


class DiscordEntityFetcher:
    """Utility class for fetching Discord entities with proper error handling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    async def _safe_fetch[T](fetch_callable: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T | None:
        """
        A generic and reusable wrapper to safely execute a fetch coroutine.

        It catches common exceptions (NotFound, Forbidden, HTTPException) that occur
        when an entity cannot be fetched, returning None in those cases.

        Args:
            fetch_callable: The coroutine function to execute (e.g., guild.fetch_member).
            *args: Positional arguments to pass to the fetch_callable.
            **kwargs: Keyword arguments to pass to the fetch_callable.

        Returns:
            The fetched Discord entity, or None if an error occurred.
        """
        try:
            return await fetch_callable(*args, **kwargs)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def fetch_reaction_action_event(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> ReactionActionEvent | None:
        if not (guild := await self.fetch_guild(payload.guild_id)):
            return None

        if not (member := await self.fetch_member(guild, payload.user_id)):
            return None

        if not (channel := await self.fetch_messageable_channel(payload.channel_id)):
            return None

        if not (message := await self.fetch_message(channel, payload.message_id)):
            return None

        if not (reaction := await self.fetch_reaction(message, payload.emoji)):
            return None

        return ReactionActionEvent(reaction, member)

    async def fetch_guild(self, guild_id: int | None) -> discord.Guild | None:
        """
        Fetches a guild by ID, checking the cache first, then falling back to a safe API call.
        """
        if guild_id is None:
            return None

        # Prioritize the cache for efficiency
        guild = self.bot.get_guild(guild_id)
        if guild:
            return guild

        return await self._safe_fetch(self.bot.fetch_guild, guild_id)

    async def fetch_member(self, guild: discord.Guild, user_id: int | None) -> discord.Member | None:
        """Safely fetches a member from a given guild using the generic helper."""
        if user_id is None:
            return None

        # Prioritize the cache for efficiency
        member = discord.utils.get(guild.members, id=user_id)
        if member:
            return member

        return await self._safe_fetch(guild.fetch_member, user_id)

    async def fetch_messageable_channel(self, channel_id: int | None) -> discord.abc.Messageable | None:
        """Safely fetches a channel by ID and verifies it is messageable."""
        if channel_id is None:
            return None

        channel = await self._safe_fetch(self.bot.fetch_channel, channel_id)

        # We still need to perform the type check after a successful fetch
        if isinstance(channel, discord.abc.Messageable):
            return channel
        return None

    async def fetch_message(self, channel: discord.abc.Messageable, message_id: int | None) -> discord.Message | None:
        """Fetch a message from a channel."""
        if message_id is None:
            return None

        return await self._safe_fetch(channel.fetch_message, message_id)

    async def fetch_reaction(self, message: discord.Message, emoji: discord.PartialEmoji) -> discord.Reaction | None:
        """Get the specific reaction from the message."""
        return discord.utils.find(lambda reaction: str(reaction.emoji) == str(emoji), message.reactions)
