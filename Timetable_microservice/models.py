from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Timetable(BaseModel):
    hospitalId: int
    doctorId: int
    start: datetime
    to: datetime
    room: str


class UpdateTimetable(Timetable):
    hospitalId: Optional[int]
    doctorId: Optional[int]
    start: Optional[datetime]
    to: Optional[datetime]
    room: Optional[str]


class TimePeriod(BaseModel):
    start: int
    to: int


class TimeSelect(BaseModel):
    time: int
