from pydantic import BaseModel
from typing import List, Optional


class Tokens(BaseModel):
    jwt_access_token: str
    jwt_refresh_token: str


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


class Success(BaseModel):
    success: bool
