from fastapi import APIRouter, HTTPException, Request, Response

from os import environ as pyenv
from starlette import status
import requests as req

from models import Hospital, UpdateHospital
import db_manager

hospital_app = APIRouter()


@hospital_app.get('/api/Hospitals')
async def get_hospital(start: int, count: int):
    if not req.get('http://localhost/api/Authentication/Validate').json()['success']:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {'hospital_ids': await db_manager.get_all_hospital(start, count)}


@hospital_app.get('/api/Hospitals/{hospital_id}')
async def get_hospital_id(hospital_id: int):
    if not req.get('http://localhost/api/Authentication/Validate').json()['success']:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {'hospital': await db_manager.get_hospital_id(hospital_id)}


@hospital_app.get('/api/Hospitals/{hospital_id}/Rooms')
async def get_rooms(hospital_id: int):
    if not req.get('http://localhost/api/Authentication/Validate').json()['success']:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {'rooms': await db_manager.get_hospital_rooms(hospital_id)}

@hospital_app.post('/api/Hospitals')
async def add_hospital(hospital: Hospital):
    if not req.get('http://localhost/api/Authentication/Validate').json()['success']:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if 'admin' not in req.get('http://localhost/api/Authentication/Validate').json()['roles']:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not db_manager.add_hospital(hospital.model_dump()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

