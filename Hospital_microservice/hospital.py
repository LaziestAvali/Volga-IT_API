from fastapi import APIRouter, HTTPException, Request, Response

from os import environ as pyenv
from starlette import status
import requests as req

from Hospital_microservice.models import *
from Hospital_microservice import db_manager

hospital_app = APIRouter()

@hospital_app.get('/api/Hospitals')
async def get_hospital(start: int, count: int):
    if req.get('http://localhost/api/Authentication/Validate'):
        return await db_manager.get_all_hospital(start, count)