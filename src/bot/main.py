import asyncio

import discord

from bot.adapters.database.database import create_tables
from bot.core.bot import ZloutekBot
from bot.core.settings import settings


async def main() -> None:
    await create_tables()

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = ZloutekBot(command_prefix="!", intents=intents)

    await bot.start(settings.bot_token)


if __name__ == "__main__":
    asyncio.run(main())
