from fastapi import APIRouter, HTTPException, Request, Response

from Account_microservice.models import BaseUser, LoginUser, UpdateUser, FullUser, UserIds
from Account_microservice import db_manager

from typing import Literal
import jwt
from os import environ as pyenv
from starlette import status
import datetime as dt


account_app = APIRouter()


def create_token(types: Literal['access', 'refresh'], payload: dict) -> str:
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

async def validate_token(request: Request, response: Response) -> bool:
    try:
        access_token = request.cookies.get('jwt_access_token')
        print(access_token)
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        payload = jwt.decode(access_token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        # любой токен кроме аксес будет отклонён
        if payload['type'] != 'access':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid token')
        # проверка если токен просрочен. Если да, запрашиваю его обновление
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= 60*10:
            refresh_token = request.cookies.get('jwt_refresh_token')
            new_access_token, new_refresh_token = update_tokens(refresh_token)
            response.set_cookie('jwt_access_token', new_access_token)
            response.set_cookie('jwt_refresh_token', new_refresh_token)
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

async def autorization(token: str, role: list | tuple):
    decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
    user = await db_manager.get_user(decoded_token)
    for user_role in user['roles']:
        if user_role in role:
            return
    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)

@account_app.post('/api/Authentication/SignUp')
async def sign_up(response: Response, payload: LoginUser):
    payload = payload.model_dump()
    full_payload = payload | {'roles': ['user']}
    if not await db_manager.add_user(full_payload):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
    payload = {'login': payload['login'], 'password': payload['password']}
    response.set_cookie(key='jwt_access_token', value=create_token('access', payload), httponly=True)
    response.set_cookie(key='jwt_refresh_token', value=create_token('refresh', payload), httponly=True)


@account_app.post('/api/Authentication/SignIn', status_code=status.HTTP_200_OK)
async def sign_in(response: Response, payload: BaseUser):
    payload = payload.model_dump()
    if await db_manager.user_in_db(payload):
        response.set_cookie(key='jwt_access_token', value=create_token('access', payload), httponly=True)
        response.set_cookie(key='jwt_refresh_token', value=create_token('refresh', payload), httponly=True)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@account_app.put('/api/Authentication/SignOut', status_code=status.HTTP_200_OK)
async def sign_out(request: Request, response: Response):
    if validate_token(request, response):
        response.delete_cookie(key='jwt_access_token')
        response.delete_cookie(key='jwt_refresh_token')

@account_app.get('/api/Authentication/Validate', status_code=status.HTTP_200_OK)
async def validate(request: Request, response: Response):
    if await validate_token(request, response):
        return {'success': True}
    return {'success': False}

@account_app.post('/api/Authentication/Refresh', status_code=status.HTTP_200_OK)
async def refresh(request: Request, response: Response):
    new_access_token, new_refresh_token = update_tokens(request.cookies.get('jwt_refresh_token'))
    response.set_cookie(key='jwt_access_token', value=new_access_token, httponly=True)
    response.set_cookie(key='jwt_refresh_token', value=new_refresh_token, httponly=True)

@account_app.get('/api/Accounts/Me', status_code=status.HTTP_200_OK)
async def get_info(request: Request, response: Response):
    if await validate_token(request, response):
        token = request.cookies.get('jwt_access_token')
        return await db_manager.get_user(jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256']))

@account_app.put('/api/Accounts/Update', status_code=status.HTTP_200_OK)
async def update(request: Request, response: Response, payload: UpdateUser):
    if await validate_token(request, response):
        token = request.cookies.get('jwt_access_token')
        decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        payload = payload.model_dump()
        if decoded_token['password'] != payload['password']:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        payload['login'] = decoded_token['login']
        payload['firstName'] = decoded_token['firstName']
        payload['lastName'] = decoded_token['lastName']
        await db_manager.update_user(payload)

@account_app.get('/api/Accounts', status_code=status.HTTP_200_OK)
async def get_accounts(request: Request, response: Response, body: UserIds):
    if await validate_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await autorization(token, ['admin'])
        payload = body.model_dump()
        finish = []
        start = int(payload['start'])
        for account in range(payload['count']):
            finish.append(await db_manager.get_user_by_id(start+account))
        return {'users': finish}

@account_app.post('/api/Accounts', status_code=status.HTTP_201_CREATED)
async def new_account(request: Request, response: Response, body: FullUser):
    if validate_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await autorization(token, ['admin'])
        if not await db_manager.add_user(body.model_dump()):
            HTTPException(status.HTTP_405_METHOD_NOT_ALLOWED)

@account_app.put('/api/Accounts/{user_id}')
async def update_admin(request: Request, response: Response, body: FullUser, user_id: int):
    if validate_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await autorization(token, ['admin'])
        payload = body.model_dump()
        await db_manager.update_user_by_id(user_id, payload)

@account_app.delete('/api/Accounts/{user_id}')
async def safe_delete(request: Request, response: Response, user_id: int):
    pass
