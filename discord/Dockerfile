FROM python:3.11.4-slim

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot bot --create-home && \
    rm -rf /var/cache/* /var/log/*

USER bot
WORKDIR /home/bot

RUN pip install --upgrade --user pip && rm -rf /home/bot/.cache
RUN pip install --user pipenv && rm -rf /home/bot/.cache
RUN rm -rf /home/bot/.cache

ENV PATH="/home/bot/.local/bin:$PATH"

COPY --chown=bot:bot Pipfile Pipfile.lock ./
COPY --chown=bot:bot PyLadiesBot ./PyLadiesBot

RUN pipenv sync && \
    rm -rf /home/bot/.cache

ENTRYPOINT ["pipenv", "run", "python", "PyLadiesBot/bot.py"]
