"""One-off bot commands.

Appropriate for triggering bot actions based on API requests to this bot system,
such as events from a web portal.
"""

import os
from enum import Enum
from pathlib import Path

from bot import _get_intents
from configuration import Config
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
from helpers import DiscordLogger

load_dotenv(Path(__file__).resolve().parent.parent / ".secrets")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

config = Config()


class Action(Enum):
    ASSIGN_VOLUNTEER = 0


class Bot(commands.Bot):

    def __init__(self, action: Action, discord_id: int):
        intents = _get_intents()
        # Not sure how to do class based oneoff connections
        # May just use non way here: https://discordpy.readthedocs.io/en/stable/quickstart.html
        super().__init__(command_prefix="", intents=intents)
        self.channels = {}
        self.action = action
        self.payload_discord_id = discord_id
        self.discord_logger = DiscordLogger("oneoff", self)

    @property
    def method_mapping(self) -> dict:
        return {Action.ASSIGN_VOLUNTEER.value: self.assign_volunteer}

    async def on_ready(self):
        self.guild = self.get_guild(config.GUILD_ID)
        await self.discord_logger.info(
            f"Executing one-off command {self.action.name} on discord ID {self.payload_discord_id} with user {self.user.name} (ID={self.user.id})"
        )
        if not self.guild:
            _msg = f"No GUILD found for {config.GUILD_ID}!"
            await self.discord_logger.critical(_msg)
            raise AssertionError(_msg)
        await self.discord_logger.info(f"Using GUILD {self.guild}")
        await self.method_mapping[self.action.value](self.payload_discord_id)
        await self.close()

    async def assign_volunteer(self, discord_id: int):
        # TODO Make DRY
        member = self.guild.get_member(discord_id)
        if not member:
            _msg = f"Member not found for ID {discord_id}"
            await self.discord_logger.critical(_msg)
            raise AssertionError(_msg)
        role = get(self.guild.roles, id=config.ROLES_VOLUNTEERS)
        if not role:
            _msg = f"Role not found for ID {discord_id}"
            await self.discord_logger.critical(_msg)
            raise AssertionError(_msg)
        await member.add_roles(role)
        await self.discord_logger.info(
            f"Successfully assigned the {role.mention} role to {member.mention}."
        )


async def assign_volunteer(discord_user_id: int):
    bot = Bot(action=Action.ASSIGN_VOLUNTEER, discord_id=discord_user_id)
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)
