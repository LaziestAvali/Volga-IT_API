from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class History(BaseModel):
    date: datetime
    pacientId: int
    hospitalId: int
    doctorId: int
    room: str
    data: str

class UpdateHistory(History):
    date: Optional[datetime]
    pacientId: Optional[int]
    hospitalId: Optional[int]
    doctorId: Optional[int]
    room: Optional[str]
    data: Optional[str]
