from fastapi import APIRouter, HTTPException, Request

from starlette import status
import requests as req

from models import *
import db_manager

history_app = APIRouter()

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

def validate_history(payload: dict, token: str):
    r = req.get(f'http://hospital_service:8000/api/Hospitals/{payload['hospitalId']}',headers={'jwt_access_token': token})
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # существует ли комната
    r = req.get(f'http://hospital_service:8000/api/Hospitals/{payload['hospitalId']}/Rooms',headers={'jwt_access_token': token})
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # существует ли доктор
    r = req.get(f'http://account_service:8000/api/Doctors/{payload["doctorId"]}/', headers={'jwt_access_token': token})
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@history_app.get('/api/History/Account/{account_id}', status_code=status.HTTP_200_OK)
async def get_all_history(request: Request, account_id: int):
    validate(request)
    token = request.headers.get('jwt_access_token')
    r = req.get('http://account_service:8000/api/Accounts/Me', headers={'jwt_access_token': token})
    if (not any(role in ['Doctor'] for role in authorization(request))) and (r.json()['id'] != account_id):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    return await db_manager.get_short_histories(account_id)

@history_app.get('/api/History/{history_id}', status_code=status.HTTP_200_OK, response_model=History)
async def get_history(request: Request, history_id: int):
    validate(request)
    token = request.headers.get('jwt_access_token')
    r = req.get('http://account_service:8000/api/Accounts/Me', headers={'jwt_access_token': token})
    result = await db_manager.get_history_id(history_id)
    if (not any(role in ['Doctor'] for role in authorization(request))) and (r.json()['id'] != result[2]):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    return {'date': result[1], 'pacientId': result[2], 'hospitalId': result[3], 'doctorId': result[4], 'room': result[5], 'data': result[6]}

@history_app.post('/api/History/', status_code=status.HTTP_201_CREATED)
async def create_history(request: Request, history: History):
    validate(request)
    if not any(role in ['Doctor', 'Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    payload = history.model_dump()
    payload['date'] = payload['date'].replace(tzinfo=None)
    token = request.headers.get('jwt_access_token')
    validate_history(payload, token)
    return await db_manager.new_history(payload)

@history_app.put('/api/History/{history_id}', status_code=status.HTTP_200_OK)
async def update_history(request: Request, history: UpdateHistory, history_id: int):
    validate(request)
    if not any(role in ['Doctor', 'Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    payload = history.model_dump()
    payload['date'] = payload['date'].replace(tzinfo=None)
    token = request.headers.get('jwt_access_token')
    validate_history(payload, token)
    await db_manager.update_history(history_id, payload)