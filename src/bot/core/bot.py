import discord
from discord.ext import commands


class ZloutekBot(commands.Bot):
    def __init__(self, command_prefix: str, intents: discord.Intents) -> None:
        super().__init__(command_prefix, intents=intents)

    async def on_ready(self) -> None:
        assert self.user
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
