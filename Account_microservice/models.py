from pydantic import BaseModel
from typing import List, Optional


class BaseUser(BaseModel):
    login: str
    password: str


class LoginUser(BaseUser):
    firstName: str
    lastName: str


class UpdateUser(LoginUser):
    login: None
    password: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None


class FullUser(LoginUser):
    roles: List[str]


class UpdateFullUser(FullUser):
    login: None = None
    password: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    roles: Optional[List[str]] = None
