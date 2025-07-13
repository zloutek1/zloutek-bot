import discord
from discord.ext import commands


class ZloutekBot(commands.Bot):
    def __init__(self, command_prefix: str, intents: discord.Intents) -> None:
        super().__init__(command_prefix, intents=intents)

    async def on_ready(self) -> None:
        if not self.user:
            raise ValueError("Bot must be a user")

        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
