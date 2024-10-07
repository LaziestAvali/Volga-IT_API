from pydantic import BaseModel
from typing import List, Optional


class BaseUser(BaseModel):
    login: str
    password: str

class LoginUser(BaseUser):
    firstName: str
    lastName: str

class UpdateUser(LoginUser):
    login: None = None

class FullUser(BaseUser):
    roles: List[str]

class UserIds(BaseModel):
    start: int
    count: int
