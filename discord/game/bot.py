import json
import shutil
import discord
from datetime import datetime
from discord.ext import commands, tasks

import random
import asyncio
import tomllib
from pathlib import Path
import pandas as pd


CONFIG_PATH = Path("config.toml")
with CONFIG_PATH.open("rb") as f:
    config = tomllib.load(f)

DB = pd.read_csv("clean_db.csv")


def normalize_name(s: str) -> str:
    _name = s.lower().replace('pyladies', '').replace(" ", "_")
    return f"{_name}.png"


def _get_intents() -> discord.Intents:
    """Get the desired intents for the bot."""
    intents = discord.Intents.all()
    intents.presences = False
    intents.dm_typing = False
    intents.dm_reactions = False
    intents.invites = False
    intents.integrations = False
    return intents


class Bot(commands.Bot):
    def __init__(self, db: pd.DataFrame):
        intents = _get_intents()
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)
        self.guild = None
        self.channels = dict()
        self.user_state: dict = dict()
        self.user_file_path = Path("users.json")
        self.db = db

    def on_ready(self):
        # Load dictionary
        if self.user_file_path.exists():
            with self.user_file_path.open("r") as f:
                self.user_state = json.loads(f.read())


        print("Read chapters:", self.db.shape[0])
        self.backup.start()

    @tasks.loop(minutes=10)
    async def backup(self):
        bak_dir = Path("bak")
        if not bak_dir.exists():
            bak_dir.mkdir()

        # Backup
        if self.user_file_path.exists():
            print("Backing up file")
            dt = int(datetime.now().timestamp())

            dst = bak_dir / f"{self.user_file_path}.bak.{dt}"
            shutil.copyfile(self.user_file_path, str(dst))

        # Save dictionary
        with self.user_file_path.open("w") as f:
            print("Writing new score file")
            json.dump(self.user_state, f)

    async def close(self):
        await super().close()

        await self.backup()


class OptionButton(discord.ui.Button["Option"]):
    def __init__(
        self,
        bot: commands.Bot,
        label: str,
        row: int = 0,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        correct=False,
    ):
        super().__init__(style=style, label="\u200b", row=row)
        self.row = row
        self.label = label
        self.style = style
        self.correct = correct
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None

        messages_correct = [
            "## That's correct!",
            "## Good guess ;)",
            "## Perfect!",
            "## You are...correct!",
            "## Correct answer",
            "## It seems you knew the logo!",
            "## Too easy? you are correct :D",
        ]

        messages_incorrect = [
            "## No, that's incorrect",
            "## mmm maybe next time",
            "## Sadly, that's incorrect",
            "## Almost, but no",
            "## Better to try again",
            "## Wrong answer",
            "## The logo was maybe difficult to guess :(",
        ]

        emoji_correct = "\N{WHITE HEAVY CHECK MARK}"
        emoji_incorrect = "\N{CROSS MARK}"
        emoji_exclamation = "\N{HEAVY EXCLAMATION MARK SYMBOL}"

        user_id = str(interaction.user.id)
        img = None

        if self.bot.user_state[user_id]["playing"]:
            if self.correct:
                embed = discord.Embed(
                    title=f"{emoji_correct} Correct!",
                    colour=0xDA373C,
                    description=random.choice(messages_correct),
                )
                self.bot.user_state[user_id]["correct"] += 1
                self.bot.user_state[user_id]["seen"].append(self.label)
                img = discord.File(
                    f"img/logos/{normalize_name(self.label)}",
                    filename="revealed.png",
                )
                embed.set_image(url="attachment://revealed.png")
            else:
                embed = discord.Embed(
                    title=f"{emoji_incorrect} Incorrect",
                    colour=0xDA373C,
                    description=random.choice(messages_incorrect),
                )
                self.bot.user_state[user_id]["incorrect"] += 1

            embed.add_field(
                name="Wait until these messages dissapear, before playing again",
                value="",
                inline=False,
            )
            self.bot.user_state[user_id]["playing"] = False
        else:
            embed = discord.Embed(
                title=f"{emoji_exclamation} Oops...",
                colour=0xDA373C,
                description="You already submitted your answer.\nOnce the messages dissapear, you can try again!",
            )

        if img is not None:
            await interaction.response.send_message(embed=embed, file=img, ephemeral=True, delete_after=4)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=4)


class ScoreButton(discord.ui.Button["Role"]):
    def __init__(
        self,
        bot,
        channel_id,
        x: int,
        y: int,
        label: str,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
    ):
        super().__init__(style=style, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.label = label
        self.style = style
        self.bot = bot
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None

        # Setting variable for new users
        user_id = str(interaction.user.id)
        if user_id not in self.bot.user_state:
            # No registry
            title = "No score found"
            desc = (
                "There is **no registry** of your score.\n"
                f"Start playing in the <#{self.channel_id}>"
            )
        else:
            user_data = self.bot.user_state[user_id]
            _correct = user_data["correct"]
            _incorrect = user_data["incorrect"]
            points = _correct - int(_incorrect // 2)
            title = "You score is"
            seen = "\n- ".join(user_data["seen"])
            desc = (
                f"## {points} points\n\n"
                f"You have '{_correct}' correct answers\n"
                f"and '{_incorrect}' incorrect answers.\n\n"
                f"and you got right the following chapters:\n- {seen}"
            )

        embed = discord.Embed(
            title=title,
            colour=0xDA373C,
            description=desc,
        )

        await interaction.response.send_message(
            embed=embed, ephemeral=True, delete_after=8
        )

class SimpleButton(discord.ui.Button["Role"]):
    def __init__(
        self,
        bot,
        x: int,
        y: int,
        label: str,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
    ):
        super().__init__(style=style, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.label = label
        self.style = style
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None

        # Setting variable for new users
        user_id = str(interaction.user.id)
        if user_id not in self.bot.user_state:
            print(f"User '{user_id}' not found. Creating registry")
            self.bot.user_state[user_id] = dict()
            self.bot.user_state[user_id]["correct"] = 0
            self.bot.user_state[user_id]["incorrect"] = 0
            self.bot.user_state[user_id]["seen"] = []

        self.bot.user_state[user_id]["playing"] = True

        embed = discord.Embed(
            title="You have 8 seconds!",
            colour=0xDA373C,
            description="Which chapter is this one?",
        )

        print("Setting up Game")
        # Random choice
        seen = self.bot.db["Name"].isin(self.bot.user_state[user_id]["seen"])
        random_row = self.bot.db[~seen].sample(n=1).to_dict("records")[0]
        print(f"Random row: {random_row}")

        options = self.bot.db[(~seen)&(self.bot.db["Name"] != random_row["Name"])].sample(n=2)["Name"].to_list()

        print("Options:", options)
        options.append(random_row["Name"])
        random.shuffle(options)
        print("Options (random):", options)

        img = discord.File(
            f"img/logos_anonymous/{random_row['File']}",
            filename="secret.png",
        )
        embed.set_image(url="attachment://secret.png")

        view = discord.ui.View(timeout=None)
        for o in options:
            view.add_item(OptionButton(bot, label=o, correct=o == random_row["Name"]))

        await interaction.response.send_message(
            embed=embed, view=view, file=img, ephemeral=True, delete_after=8
        )


class Game(commands.Cog):
    def __init__(self, bot: commands.Bot, channel_id: int, ranking_channel_id: int):
        self.bot = bot
        self.channel_id = channel_id
        self.ranking_channel_id = ranking_channel_id
        self.guild = None

    # 5 minutes
    @tasks.loop(minutes=5)
    async def update_ranking(self):
        print(f"{datetime.now()} : Updating ranking")
        ranking_channel = self.bot.get_channel(self.ranking_channel_id)

        # Update ranking
        ranking_embed = discord.Embed(
            title="Top 10 PyLadies Game",
            colour=0xFF8331,
        )
        await ranking_channel.purge()
        ranking = dict(sorted(self.bot.user_state.items(),
                       key=lambda x: x[1]["correct"] - int(x[1]["incorrect"] // 2), reverse=True))
        for i, (k, v) in enumerate(ranking.items()):
            if i >= 10:
                break
            points = v["correct"] - int(v["incorrect"] // 2)
            ranking_embed.add_field(
                name="",
                value=f"{i + 1}. <@{k}> ({points} points)",
                inline=False,
            )

        await ranking_channel.send(embed=ranking_embed)

    @commands.Cog.listener()
    async def on_ready(self):

        channel = self.bot.get_channel(self.channel_id)
        await channel.purge()

        # Starting ranking timer
        self.update_ranking.start()

        emoji_diamond = "\N{SMALL ORANGE DIAMOND}"
        emoji_party = "\N{FACE WITH PARTY HORN AND PARTY HAT}"
        emoji_trophy = "\N{TROPHY}"

        view = discord.ui.View(timeout=None)
        view.add_item(
            SimpleButton(self.bot, 0, 0, "Guess the chapter")
        )
        view.add_item(
            ScoreButton(self.bot, self.channel_id, 0, 0, "Check your score",
                        style=discord.ButtonStyle.secondary)
        )

        embed = discord.Embed(
            title="How many PyLadies chapters logos do you know?",
            colour=0xFF8331,
        )

        embed.add_field(
            name=f"{emoji_diamond} How does it work?",
            value="You will get a random PyLadies logo and you will have **8 seconds** to guess to which chapter it belongs",
            inline=False,
        )

        embed.add_field(
            name=f"{emoji_diamond} How does the points work?",
            value="You get **+1 point** by one correct answer, and **-1 point** by two incorrect answer.",
            inline=False,
        )

        embed.add_field(
            name=f"{emoji_diamond} How many times I can play?",
            value="All the ones you want! Just press the 'Guess the chapter' button.",
            inline=False,
        )

        embed.add_field(
            name=f"{emoji_trophy} Prizes!",
            value="The **top 3 players** will get a PyCharm License!.",
            inline=False,
        )

        embed.add_field(
            name=f"Ready to play? {emoji_party}",
            value="",
            inline=False,
        )

        await channel.send(embed=embed, view=view)

    async def cog_unload(self) -> None:
        channel = self.bot.get_channel(self.channel_id)
        await channel.purge()

        def create_message(body: str) -> discord.Embed:
            orange = 0xE5287A
            return discord.Embed(
                title="PyLadiesCon Game 🎉🐍",
                description=body,
                color=orange,
            )

        await channel.send(
            embed=create_message("The game bot is currently offline. " "Stay tuned!.")
        )


async def main():
    async with bot:
        await bot.add_cog(
            Game(bot, config["game"]["CHANNEL_ID"], config["game"]["RANKING_CHANNEL_ID"])
        )
        await bot.start(config["general"]["TOKEN"])


if __name__ == "__main__":
    bot = Bot(DB)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, exiting...")
