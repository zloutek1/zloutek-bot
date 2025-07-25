import asyncio

import discord

from bot.core.bot import ZloutekBot
from bot.core.database import create_tables
from bot.core.logging import setup_logging
from bot.core.settings import settings


async def main() -> None:
    setup_logging()

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = ZloutekBot(command_prefix="!", intents=intents)
    await bot.load_extension("bot.starboard")

    await create_tables()

    await bot.start(settings.bot_token)


if __name__ == "__main__":
    asyncio.run(main())
