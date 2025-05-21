from pydantic import BaseModel


class Result(BaseModel):
    is_success: bool


class Token(BaseModel):
    token: str


class DiscordUser(Token):
    id: int
