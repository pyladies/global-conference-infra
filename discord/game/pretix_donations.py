import os
import logging
import requests
from discord import Embed
from collections import Counter

from discord.ext import commands, tasks

from configuration import Config
config = Config()
_logger = logging.getLogger(f"bot.{__name__}")


class PretixDonations(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        _logger.info("Cog 'PretixDonations' has been initialized")

        self.channel_id = config.DONATIONS_CHANNEL_ID
        self.pretix_token = config.PRETIX_TOKEN
        _logger.info(f"Channel ID for Donations: {self.channel_id}")

    @tasks.loop(minutes=15)
    async def send_notification(self):
        channel = self.bot.get_channel(self.channel_id)

        total = 0
        donors = dict()
        try:
            url = config.PRETIX_URL
            i = 1
            while True:
                _logger.info(f"Fetching data for donations from page {i}")
                response = requests.get(url, headers={"Authorization": f"Token {self.pretix_token}"})
                data = response.json()
                for v in data["results"]:
                    email = v["email"]
                    for p in v["payments"]:
                        amount = float(p["amount"])
                        if amount > 0 and p["state"] == "confirmed":
                            donors[email] = amount
                            total += amount
                if not data["next"]:
                    break
                url = data["next"]
                i += 1
        except Exception as e:
            _logger.error(f"Found error while fetching data: {e}")

        if total > 0:
            message = f"# {total} USD\n\n## Number of donations per amount\n\n"
            sorted_donations = sorted(dict(Counter(donors.values())).items(), reverse=True)
            for i, sd in enumerate(sorted_donations):
                s = "people"
                if sd[1] == 1:
                    s = "person"
                if i == 0:
                    emoji = "\N{FIRST PLACE MEDAL}"
                    s += f" {emoji}"
                elif i == 1:
                    emoji = "\N{SECOND PLACE MEDAL}"
                    s += f" {emoji}"
                elif i == 2:
                    emoji = "\N{THIRD PLACE MEDAL}"
                    s += f" {emoji}"
                message += f"- **$ {int(sd[0])} USD** ({sd[1]} {s})\n"

            message += "\n### \N{HEAVY BLACK HEART} Donate now https://pretix.eu/pyladiescon/2025/"
            message += ("\n\n **Please note**: In case you donated via "
                        "https://2025.conference.pyladies.com/en/donate/ "
                        "we will get the final amount after the conference")

            # Get channel
            _logger.info("Removing content from the donations channel")
            await channel.purge()
            e = Embed(title="Conference Donations", description=message, color=0xb42a34)
            await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_ready(self):

        self.send_notification.start()
