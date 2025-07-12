import discord
from discord.ext import commands

type PurgableChannel = discord.Thread | discord.TextChannel | discord.channel.VocalGuildChannel


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def purge(self, ctx: commands.Context[commands.Bot], amount: int) -> None:
        if not isinstance(ctx.channel, PurgableChannel.__value__):
            return

        await ctx.channel.purge(limit=amount + 1)


async def setup(bot: commands.Bot) -> None:
    cog = AdminCog(bot)
    await bot.add_cog(cog)
