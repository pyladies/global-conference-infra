from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class DaySchedule(BaseModel):
    """Schedule of a single day of PyLadiesCon"""

    rooms: list[str]
    events: list[Session | Break]


class Schedule(BaseModel):
    """Complete schedule of PyLadiesCon"""

    days: dict[date, DaySchedule]



class Session(BaseModel):
    """Session in the PyLadiesCon schedule"""

    code: str
    duration: int
    event_type: str
    level: str
    rooms: list[str]
    session_type: str
    slug: str
    speakers: list[Speaker]
    start: datetime
    title: str
    track: str | None
    youtube_url: str
    website_url: str

    def __hash__(self) -> int:
        return hash(self.code + str(self.start))

class Break(BaseModel):
    """Break in the PyLadiesCon schedule"""

    event_type: str
    title: str
    duration: int
    rooms: list[str]
    start: datetime



class Speaker(BaseModel):
    """Speaker of a Session"""

    code: str
    name: str
    avatar: str
    website_url: str
