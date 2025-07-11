import asyncio

import discord
from discord.ext import commands

from bot.adapters.discord.cogs.welcome import WelcomeCog
from bot.core.config import settings
from bot.features.welcome.services import WelcomeService


async def main() -> None:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    await bot.add_cog(WelcomeCog(bot=bot, welcome_service=WelcomeService()))

    await bot.start(settings.bot_token)


if __name__ == "__main__":
    asyncio.run(main())
