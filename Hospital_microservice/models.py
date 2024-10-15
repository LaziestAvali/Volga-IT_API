from pydantic import BaseModel
from typing import Optional, List


class Hospital(BaseModel):
    name: str
    address: str
    contactPhone: str
    rooms: List[str]


class UpdateHospital(Hospital):
    name: Optional[str] = None
    address: Optional[str] = None
    contactPhone: Optional[str] = None
    rooms: Optional[str] = None
