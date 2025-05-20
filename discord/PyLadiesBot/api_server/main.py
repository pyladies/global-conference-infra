from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from helpers import _setup_logging
from oneoff import main

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".secrets")

app = FastAPI()

_setup_logging()


@app.get("/")
async def root():
    await main()
    return {"message": "Hello World"}
