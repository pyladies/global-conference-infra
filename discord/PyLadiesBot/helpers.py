import logging
import sys
import textwrap

import configuration
from configuration import Config
from discord import Message
from discord.abc import Messageable
from discord.ext.commands import Bot

config = Config()


async def safe_send_message(target: Messageable, text: str) -> list[Message]:
    """Safely send a message to the given messageable target.
    The utility of this is function, is that the message will be split into multiple parts
    if its too long.
    """
    messages = []
    for part in textwrap.wrap(
        text,
        width=2000,
        expand_tabs=False,
        replace_whitespace=False,
        drop_whitespace=False,
    ):
        message = await target.send(part)
        messages.append(message)
    return messages


class DiscordLogger:
    """Wrapper for the configured project logger, that also sends the same logs to discord.

    Use any of the logging level methods, just like in the standard library on the
    instantiated object.

    Automatically prefixes `bot.` to the name provided for the logger.

    Requires a bot object to be instantiated and passed into it.

    For example:
    ```python
        discord_logger = DiscordLogger(__name__, self.bot)
        discord_logger.info("The 'ping' command has been triggered!")
        discord_logger.error("A problem has occurred!")
    ```
    """

    def __init__(self, name: str, bot: Bot):
        self.name = f"bot.{name}"
        self.bot = bot
        self.logger = logging.getLogger(self.name)

    def __getattr__(self, method_name: str):
        logging_types = {
            "debug",
            "info",
            "warning",
            "warn",
            "error",
            "exception",
            "critical",
            "fatal",
        }
        if method_name not in logging_types:
            raise AttributeError(f"Logging type must be one of {logging_types}")

        def _log(message: str):

            async def inner():
                logging_method = getattr(self.logger, method_name)
                logging_method(message)
                channel = self.bot.get_channel(config.log_channel)
                prefix = f"{self.name} - {method_name.upper()} - "
                await safe_send_message(channel, f"{prefix}{message}")

            return inner()

        return _log


def _setup_logging() -> None:
    """Set up a basic logging configuration."""
    config = configuration.Config()

    # Create a stream handler that logs to stdout (12-factor app)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)

    # Configure the root logger with the stream handler and log level
    root_logger = logging.getLogger()
    root_logger.addHandler(stream_handler)
    root_logger.setLevel(config.LOG_LEVEL)
