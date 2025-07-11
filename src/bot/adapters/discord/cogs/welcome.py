from bot.features.welcome.services import WelcomeService
from discord.ext import commands


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, welcome_service: WelcomeService):
        self.bot = bot
        self._service = welcome_service

    @commands.command()
    async def greet(self, ctx: commands.Context[commands.Bot]) -> None:
        """Greets the user using the welcome service."""
        if not ctx.guild:
            await ctx.send("This command only works in a server.")
            return

        greeting = self._service.generate_welcome_text(guild_id=ctx.guild.id, user_name=ctx.author.display_name)
        await ctx.send(greeting)


async def setup(bot: commands.Bot) -> None:
    welcome_service = WelcomeService()
    cog = WelcomeCog(bot, welcome_service)
    await bot.add_cog(cog)
