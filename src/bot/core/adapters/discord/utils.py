from typing import NamedTuple

import discord
from discord.ext import commands

from bot.core.adapters.discord.errors import EntityNotFoundError, ExternalServiceError


class ReactionActionEvent(NamedTuple):
    """Represents the context of a reaction event with the core fetched entities."""

    reaction: discord.Reaction
    reactor: discord.Member


class ReactionEventHydrator:
    """
    Responsible for converting raw Discord reaction events into complete
    domain objects, handling caching and API calls as needed.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def hydrate(self, payload: discord.RawReactionActionEvent) -> ReactionActionEvent:
        """
        Convert a raw reaction event into a fully-hydrated reaction event.

        This method leverages Discord's caching where possible and only makes
        API calls when necessary. It translates Discord-specific errors into
        port-level exceptions.
        """
        try:
            guild = self._get_cached_guild(payload.guild_id)
            channel = self._get_cached_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            member = await self._fetch_member_if_needed(guild, payload.user_id)
            reaction = self._find_reaction_on_message(message, payload.emoji)

            return ReactionActionEvent(reaction, member)
        except discord.NotFound as ex:
            raise EntityNotFoundError("Entity not found") from ex
        except discord.Forbidden as ex:
            raise PermissionError("Access denied") from ex
        except discord.HTTPException as ex:
            raise ExternalServiceError("External service error") from ex

    def _get_cached_guild(self, guild_id: int | None) -> discord.Guild:
        if guild_id is None:
            raise ValueError("Provided event with no guild ID")

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            raise EntityNotFoundError(f"Guild with ID {guild_id} not found")

        return guild

    def _get_cached_channel(self, channel_id: int) -> discord.abc.Messageable:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            raise EntityNotFoundError(f"Channel with ID {channel_id} not found")

        if not isinstance(channel, discord.abc.Messageable):
            raise ValueError(f"Channel with ID {channel_id} is not a messageable channel")

        return channel

    async def _fetch_member_if_needed(self, guild: discord.Guild, member_id: int) -> discord.Member:
        member = guild.get_member(member_id)
        if member is not None:
            return member

        return await guild.fetch_member(member_id)

    def _find_reaction_on_message(self, message: discord.Message, emoji: discord.PartialEmoji) -> discord.Reaction:
        reaction = discord.utils.find(lambda reaction: str(reaction.emoji) == str(emoji), message.reactions)

        if reaction is None:
            raise EntityNotFoundError(f"Reaction {emoji} not found on message {message.id}")

        return reaction
