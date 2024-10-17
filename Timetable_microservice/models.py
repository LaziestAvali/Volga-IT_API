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
    hospitalId: Optional[int] = None
    doctorId: Optional[int] = None
    start: Optional[datetime] = None
    to: Optional[datetime] = None
    room: Optional[str] = None


class TimePeriod(BaseModel):
    start: int
    to: int


class TimeSelect(BaseModel):
    time: int
