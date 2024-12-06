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
    "sprints": {
        "webhook": config['webhooks']['sprints_guidelines'],
        "title": "Sprints Guidelines",
        "message": dedent(f"""\
            1. Sprints are an activity that will run during the whole conference.
            2. The interaction will be only on Discord (on this category called `Sprints`)
            3. Each Sprint project has a Forum channel, and a Voice channel.
            3. The orientation will happen on December 6th, 20:40h UTC (check the [time here](https://time.is/UTC))
               on Discord, in the channel <#1308516681231892521>
            4. Anyone can participate!

            **Each project has their own guidelines**
            Check their first post on their channels:
            - <#1312843117174591538>
            - <#1310702448368943175>
            - <#1312846344733593630>
            - <#1312846431362617364>

            More information: https://pretalx.com/pyladiescon-2024/talk/TYVM8N/

        """)
    },
    "room_guidelines": {
        "webhook": config['webhooks']['room_guidelines'],
        "title": "Room Guidelines",
        "message": dedent(f"""\
            ## The schedule can be found [here](https://conference.pyladies.com/schedule/) and the default time is https://time.is/UTC

            **Main Stream**
            - All the sessions from `Main Stream` will be streamed on YouTube.
            - You can access [the playlist](https://www.youtube.com/playlist?list=PLOItnwPQ-eHxWh6Af6xRuKprSk_OBU0cL) directly, or wait for each announcement with the direct YouTube link in <#1314615187323617392>.
            - Use <#1308516459936223303> for text-only discussion and Q&A.
            - Use <#1308516529658134619> in case you want to have voice chat.

            **Activities & Open Spaces**
            - All the sessions from `Activities & Open Spaces` will happen on Discord in the <#1308516681231892521> channel.
            - You can use <#1308516652236804096> for text-only communication

            ## Have a question?
            Leave your message in <#1310528827449020418>
        """)
    },
}

if __name__ == "__main__":

    #for name, content in data.items():
    #    w = SyncWebhook.from_url(content["webhook"])
    #    e = Embed(title=content["title"], description=content["message"], color= 0xb42a34)
    #    w.send(embed=e)

    content = data["room_guidelines"]

    w = SyncWebhook.from_url(content["webhook"])
    e = Embed(title=content["title"], description=content["message"], color= 0xb42a34)
    w.send(embed=e)
