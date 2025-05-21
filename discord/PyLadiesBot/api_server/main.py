import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from helpers import _setup_logging
from oneoff import assign_volunteer

from PyLadiesBot.api_server.models import DiscordUser, Result

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")
BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")

_setup_logging()
app = FastAPI()


@app.post("/events/volunteer-approved")
async def volunteer_approved(body: DiscordUser) -> Result:
    is_authenticated = secrets.compare_digest(
        body.token,
        BOT_API_TOKEN,
    )
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    await assign_volunteer(body.id)
    return Result(is_success=True)
