import logging

from discord.ext import commands
from helpers import DiscordLogger

_logger = logging.getLogger(f"bot.{__name__}")


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        _logger.info("Cog 'Ping' has been initialized")
        self.discord_logger = DiscordLogger(__name__, self.bot)

    @commands.hybrid_command(name="ping", description="Ping the bot")
    async def ping_command(self, ctx: commands.Context) -> None:
        await self.discord_logger.info("The 'ping' command has been triggered!")
        await ctx.send("Pong!")
