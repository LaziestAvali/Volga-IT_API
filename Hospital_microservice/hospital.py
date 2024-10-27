from fastapi import APIRouter, HTTPException, Request

from starlette import status
import requests as req

from models import Hospital, UpdateHospital
import db_manager

hospital_app = APIRouter()


def validate(request: Request):
    token = request.headers.get('jwt_access_token')
    r = req.get('http://account_service:8000/api/Authentication/Validate', headers={'jwt_access_token': token})
    match r.status_code:
        case 401:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        case 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid token')
        case 426:
            raise HTTPException(status_code=status.HTTP_426_UPGRADE_REQUIRED)
    r_json = r.json()
    return r_json['success']

def authorization(request: Request):
    token = request.headers.get('jwt_access_token')
    r = req.get('http://account_service:8000/api/Accounts/Me', headers={'jwt_access_token': token})
    r_json = r.json()
    return r_json['roles']

@hospital_app.get('/api/Hospitals')
async def get_hospital(request: Request, start: int = 0, count: int = -1):
    if not validate(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {'hospitals': await db_manager.get_all_hospital(start, count)}


@hospital_app.get('/api/Hospitals/{hospital_id}')
async def get_hospital_id(request: Request, hospital_id: int):
    if not validate(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    hospital = await db_manager.get_hospital_id(hospital_id)
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {'hospital': hospital}


@hospital_app.get('/api/Hospitals/{hospital_id}/Rooms')
async def get_rooms(request: Request, hospital_id: int):
    if not validate(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {'rooms': await db_manager.get_hospital_rooms(hospital_id)}


@hospital_app.post('/api/Hospitals')
async def add_hospital(request: Request, hospital: Hospital):
    if not validate(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if 'Admin' not in authorization(request):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not await db_manager.add_hospital(hospital.model_dump()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@hospital_app.put('/api/Hospitals/{hospital_id}')
async def update_hospital(request: Request, hospital: UpdateHospital, hospital_id: int):
    if not validate(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if 'Admin' not in authorization(request):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not await db_manager.update_hospital(hospital_id, hospital.model_dump()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@hospital_app.delete('/api/Hospitals/{hospital_id}')
async def delete_hospital(request: Request, hospital_id: int):
    if not validate(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if 'Admin' not in authorization(request):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not await db_manager.soft_delete(hospital_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)