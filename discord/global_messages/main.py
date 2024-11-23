import tomllib
from pathlib import Path
from discord import SyncWebhook, Embed
from textwrap import dedent


with Path("config.toml").open("rb") as f:
    config = tomllib.load(f)

data = {
    "rules": {
        "webhook": config['webhooks']['rules'],
        "title": "Conference Rules",
        "message": dedent(f"""\
            1. Follow the [Code of Conduct](https://conference.pyladies.com)
            2. Use **English** to the best of your ability. Be polite if someone speaks English imperfectly.
            3. Use the name on your ticket as your display name. This will be done automatically during the
               <#{config['channel']['REG_CHANNEL_ID']}> process.

            **Reporting Incidents**
            If you notice something that needs the attention of a moderator of the community, please ping the <@&{config['roles']['CODE_OF_CONDUCT']}> role.

            See the <#{config['channel']['COC_CHANNEL_ID']}> channel to read how you can report Code of Conduct incidents.

            **Contacting the organization**
            In case of general conference questions, you can contact the <@&{config['roles']['ORGANISERS']}> or
            <@&{config['roles']['VOLUNTEERS']}> directly by mentioning the role.

            You can alternatively write an email to `pyladiescon@pyladies.com`.
        """)
    },
    "coc": {
        "webhook": config['webhooks']['code_of_conduct'],
        "title": "Code of Conduct",
        "message": dedent(f"""\
            PyLadiesCon is a community conference intended for networking and collaboration. We aim
            to provide a safe, inclusive, welcoming, and harassment-free for everyone in our
            community.

            We want all participants to have an enjoyable and fulfilling experience. Accordingly,
            all participants are expected to show respect and courtesy to other participants
            throughout the conference and at all conference-related events and activities.

            To make clear what is expected, all members of the organizing committee, attendees,
            speakers, organizers, sponsors, and volunteers at any PyLadiesCon event are required to
            conform to the following Code of Conduct as set forth by the Python Software Foundation.

            **Organizers will enforce this code throughout the event.**

            ## Our Community

            Members of the Python community are open, considerate, and respectful. Behaviors that
            reinforce these values contribute to a positive environment, and include:

            * Being open. Members of the community are open to collaboration, whether it’s on PEPs,
              patches, problems, or otherwise.
            * Focusing on what is best for the community. We’re respectful of the processes set
              forth in the community, and we work within them.
            * Acknowledging time and effort. We’re respectful of the volunteer efforts that permeate
              the Python community. We’re thoughtful when addressing the efforts of others, keeping in
              mind that often times the labor was completed simply for the good of the community.
            * Being respectful of differing viewpoints and experiences. We’re receptive to
              constructive comments and criticism, eriences and skill sets of other members contribute
              to the whole of our efforts.
            * Showing empathy towards other community members. We’re attentive in our
              communications, whether in person or online, and we’re tactful when approaching
              differing views.
            * Being considerate. Members of the community are considerate of their peers – other
              Python users.
            * Being respectful. We’re respectful of others, their positions, their skills, their
              commitments, and their efforts.
            * Gracefully accepting constructive criticism. When we disagree, we are courteous in
              raising our issues.
            * Using welcoming and inclusive language. We’re accepting of all who wish to take part
              in our activities, fostering an environment where anyone can participate and everyone
              can make a difference.

            **More Information:** Read our full Code of Conduct at
            https://conference.pyladies.com/about/#code-of-conduct
        """)
    },
}

if __name__ == "__main__":

    for name, content in data.items():
        w = SyncWebhook.from_url(content["webhook"])
        e = Embed(title=content["title"], description=content["message"], color= 0xb42a34)
        w.send(embed=e)
