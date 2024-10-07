from fastapi import APIRouter, HTTPException, Request, Response

from Account_microservice.models import BaseUser, LoginUser, UpdateUser, FullUser, AccessToken
from Account_microservice import db_manager

from typing import Literal
import jwt
from os import environ as pyenv
from starlette import status
import datetime as dt


account_app = APIRouter()


def create_token(types: Literal['access','refresh'], payload: dict) -> str:
    current_timestamp = dt.datetime.now(tz=dt.timezone.utc).timestamp()
    data = {
        'iss': 'account_microservice',
        'type': types,
        'jti': types + str(current_timestamp),
        'nbf': current_timestamp,
        'exp': current_timestamp + 60*60*24*7 if type == 'refresh' else current_timestamp + 60*10,
    }
    payload = payload | data

    return str(jwt.encode(payload, pyenv['JWT_SECRET'], algorithm='HS256'))

async def validate_token(token) -> bool:
    try:
        payload = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        # любой токен кроме аксес будет отклонён
        if payload['type'] != 'access':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid token')
        # проверка если токен просрочен. Если да, запрашиваю его обновление
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= 60*10:
            raise HTTPException(status_code=status.HTTP_426_UPGRADE_REQUIRED)
        if await db_manager.user_in_db(payload):
            return True
        return False
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

def update_tokens(token):
    try:
        payload = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        if payload['type'] != 'refresh':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= 60*60*24*7:
            raise HTTPException(status_code=status.HTTP_426_UPGRADE_REQUIRED)
        return create_token('access', payload), create_token('refresh', payload)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

def upgrade_token(token):
    if validate_token(token):
        payload = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        db_manager.get_user(payload)


@account_app.post('/api/Authentication/SignUp')
async def sign_up(response: Response, payload: LoginUser):
    response.set_cookie(key='jwt_access_token', value=create_token('access', payload.model_dump()), httponly=True)
    response.set_cookie(key='jwt_refresh_token', value=create_token('refresh', payload.model_dump()), httponly=True)
    full_payload = payload.model_dump() | {'roles': ['user']}
    await db_manager.add_user(full_payload)

@account_app.post('/api/Authentication/SignIn', status_code=status.HTTP_200_OK)
async def sign_in(response: Response, payload: BaseUser):
    if await db_manager.user_in_db(payload):
        response.set_cookie(key='jwt_access_token', value=create_token('access', payload.model_dump()), httponly=True)
        response.set_cookie(key='jwt_refresh_token', value=create_token('refresh', payload.model_dump()), httponly=True)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@account_app.put('/api/Authentication/SignOut', status_code=status.HTTP_200_OK)
async def sign_out(response: Response):
    try:
        response.delete_cookie(key='jwt_access_token')
        response.delete_cookie(key='jwt_refresh_token')
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@account_app.get('/api/Authentication/Validate', status_code=status.HTTP_200_OK)
async def validate(request: Request):
    if await validate_token(request.cookies.get('jwt_access_token')):
        return {'success': True}
    return {'success': False}

@account_app.post('/api/Authentication/Refresh', status_code=status.HTTP_200_OK)
async def refresh(response: Response, request: Request):
    new_access_token, new_refresh_token = update_tokens(request.cookies.get('jwt_refresh_token'))
    response.set_cookie(key='jwt_access_token', value=new_access_token, httponly=True)
    response.set_cookie(key='jwt_refresh_token', value=new_refresh_token, httponly=True)

@account_app.get('/api/Accounts/Me', status_code=status.HTTP_200_OK)
async def get_info(request: Request):
    token = request.cookies.get('jwt_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if await validate_token(token):
        return await db_manager.get_user(jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256']))

@account_app.put('/api/Accounts/Update', status_code=status.HTTP_200_OK)
async def update(request: Request, payload: UpdateUser):
    token = request.cookies.get('jwt_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if await validate_token(token):
        decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        if decoded_token['password'] != payload['password']:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
        payload['login'] = decoded_token['login']
        payload['firstName'] = decoded_token['firstName']
        payload['lastName'] = decoded_token['lastName']
        await db_manager.update_user(payload)

@account_app.get('/api/Accounts/{start_id}/{end_id}', status_code=status.HTTP_200_OK)
async def get_accounts(request: Request, start_id: int, end_id: int):
    token = request.cookies.get('jwt_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if await validate_token(token):
        decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        user_role = decoded_token
    ## БДШКУ СЮДА ХАЧУ
    pass
