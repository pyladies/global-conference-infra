"""One-off bot commands.

Appropriate for triggering bot actions based on API requests to this bot system,
such as events from a web portal.
"""

import os
from pathlib import Path

from bot import _get_intents
from discord.ext import commands
from dotenv import load_dotenv
from helpers import DiscordLogger

load_dotenv(Path(__file__).resolve().parent.parent / ".secrets")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


class Bot(commands.Bot):
    def __init__(self):
        intents = _get_intents()
        # Not sure how to do class based oneoff connections
        # May just use non way here: https://discordpy.readthedocs.io/en/stable/quickstart.html
        super().__init__(command_prefix="", intents=intents)
        self.guild = None
        self.channels = {}
        self.discord_logger = DiscordLogger("oneoff", self)

    async def on_ready(self):
        await self.discord_logger.info(
            f"Starting one-off command with user {self.user.name} (ID={self.user.id})"
        )
        await self.close()


async def main():
    bot = Bot()
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)
