from discord.ext import commands

from bot.core.database import async_session_factory
from bot.starboard.adapters.database.repository import OrmStarboardMapper, OrmStarboardRepository
from bot.starboard.adapters.discord.cog import StarboardCog
from bot.starboard.adapters.discord.presenter import DiscordStarboardPresenter
from bot.starboard.adapters.discord.publisher import DiscordStarboardPublisher
from bot.starboard.application.services import StarboardService


async def setup(bot: commands.Bot) -> None:
    repository = OrmStarboardRepository(session_factory=async_session_factory, mapper=OrmStarboardMapper())
    publisher = DiscordStarboardPublisher(bot)
    presenter = DiscordStarboardPresenter()

    service = StarboardService(repository, publisher, presenter)
    cog = StarboardCog(bot, service)
    await bot.add_cog(cog)
