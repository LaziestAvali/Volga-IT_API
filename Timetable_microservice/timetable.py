from fastapi import APIRouter, HTTPException, Request

from starlette import status
import requests as req

from models import Timetable, UpdateTimetable, TimePeriod, TimeSelect
import datetime as dt
import db_manager

timetable_app = APIRouter()

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

def validate_timetable(payload: dict, token: str):
    if int(payload['start'].minute) not in (0, 30):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Start time is invalid')
    if int(payload['to'].minute) not in (0, 30):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='End time is invalid')
    if payload['start'] > payload['to']:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
    if payload['to'] - payload['start'] > dt.timedelta(hours=12):
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
    r = req.get(f'http://hospital_service:8000/api/Hospitals/{payload['hospitalId']}', headers={'jwt_access_token': token})
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # существует ли комната
    r = req.get(f'http://hospital_service:8000/api/Hospitals/{payload['hospitalId']}/Rooms', headers={'jwt_access_token': token})
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # существует ли доктор
    r = req.get(f'http://account_service:8000/api/Doctors/{payload["doctorId"]}/', headers={'jwt_access_token': token})
    if r.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@timetable_app.post('/api/Timetable', status_code=status.HTTP_201_CREATED)
async def create_timetable(request: Request, payload: Timetable):
    validate(request)
    if not any(role in ['Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    payload = payload.model_dump()
    payload['start'] = payload['start'].replace(tzinfo=None)
    payload['to'] = payload['to'].replace(tzinfo=None)
    token = request.headers.get('jwt_access_token')
    validate_timetable(payload, token)
    await db_manager.new_timetable(payload)

@timetable_app.put('/api/Timetable/{timetable_id}', status_code=status.HTTP_200_OK)
async def update_timetable(request: Request, payload: UpdateTimetable, timetable_id: int):
    validate(request)
    if not any(role in ['Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if await db_manager.get_appointments_of_timetable(timetable_id):
        return HTTPException(status_code=status.HTTP_409_CONFLICT)
    payload = payload.model_dump()
    payload['start'] = payload['start'].replace(tzinfo=None)
    payload['to'] = payload['to'].replace(tzinfo=None)
    token = request.headers.get('jwt_access_token')
    validate_timetable(payload, token)
    if not await db_manager.update_timetable(payload, timetable_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@timetable_app.delete('/api/Timetable/{timetable_id}', status_code=status.HTTP_200_OK)
async def delete_timetable(request: Request, timetable_id: int):
    validate(request)
    if not any(role in ['Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not await db_manager.delete_timetable(timetable_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@timetable_app.delete('/api/Timetable/Doctor/{doctor_id}', status_code=status.HTTP_200_OK)
async def delete_by_doctor(request: Request, doctor_id: int):
    validate(request)
    if not any(role in ['Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not await db_manager.delete_by_doctor(doctor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@timetable_app.delete('/api/Timetable/Hospital/{hospital_id}', status_code=status.HTTP_200_OK)
async def delete_by_hospital(request: Request, hospital_id: int):
    validate(request)
    if not any(role in ['Admin', 'Manager'] for role in authorization(request)):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    if not await db_manager.delete_by_hospital(hospital_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@timetable_app.get('/api/Timetable/Hospital/{hospital_id}', status_code=status.HTTP_200_OK)
async def timetable_of_hospital(request: Request, payload: TimePeriod, hospital_id: int):
    validate(request)
    payload = payload.model_dump()
    payload['start'] = payload['start'].replace(tzinfo=None)
    payload['to'] = payload['to'].replace(tzinfo=None)
    return await db_manager.get_timetable_of_hospital(payload, hospital_id)

@timetable_app.get('/api/Timetable/Doctor/{doctor_id}', status_code=status.HTTP_200_OK)
async def timetable_of_doctor(request: Request, payload: TimePeriod, doctor_id: int):
    validate(request)
    payload = payload.model_dump()
    payload['start'] = payload['start'].replace(tzinfo=None)
    payload['to'] = payload['to'].replace(tzinfo=None)
    return await db_manager.get_timetable_of_doctor(payload, doctor_id)

@timetable_app.get('/api/Timetable/Hospital/{hospital_id}/Room/{room}', status_code=status.HTTP_200_OK)
async def timetable_of_room(request: Request, payload: TimePeriod, hospital_id: int, room: str):
    validate(request)
    payload = payload.model_dump()
    payload['start'] = payload['start'].replace(tzinfo=None)
    payload['to'] = payload['to'].replace(tzinfo=None)
    return await db_manager.get_timetable_of_room(payload, hospital_id, room)

@timetable_app.get('/api/Timetable/{timetable_id}/Appointments', status_code=status.HTTP_200_OK)
async def timetable_of_appointments(request: Request, timetable_id: int):
    validate(request)
    timetable = await db_manager.get_timetable_by_id(timetable_id)
    token_list = []
    time_appointment = timetable[4]
    appointments = await db_manager.get_appointments_of_timetable(timetable)
    while time_appointment < timetable[5]:
        token_list.append(time_appointment)
        time_appointment += dt.timedelta(minutes=30)
    return {'available_appointment': (i for i in token_list if i not in appointments)}

@timetable_app.post('/api/Timetable/{timetable_id}/Appointments}', status_code=status.HTTP_201_CREATED)
async def new_appointment(request: Request, payload: TimeSelect, timetable_id: int):
    validate(request)
    payload = payload.model_dump()
    payload['time'] = payload['time'].replace(tzinfo=None)
    if int(payload['time'].minute) not in (0, 30):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Start time is invalid')
    appointments = await timetable_of_appointments(request, timetable_id)
    if payload['time'] not in appointments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Appointment is not available')
    token = request.headers.get('jwt_access_token')
    user_id = req.get('http://account_service:8000/api/Accounts/Me', headers={'jwt_access_token': token}).json()['id']
    return {'id': await db_manager.new_appointment(timetable_id, user_id, payload['time'])}

@timetable_app.delete('/api/Appointment/{appointment_id}', status_code=status.HTTP_200_OK)
async def delete_appointment(request: Request, appointment_id: int):
    validate(request)
    token = request.headers.get('jwt_access_token')
    r = req.get('http://account_service:8000/api/Accounts/Me', headers={'jwt_access_token': token})
    if (not any(role in ['Admin', 'Manager'] for role in authorization(request))) and (r.json()['id'] != (await db_manager.get_appointment_by_id(appointment_id))[2]):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    await db_manager.delete_appointment(appointment_id)
