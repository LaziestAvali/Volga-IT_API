from fastapi import APIRouter, HTTPException, Request

from uuid import uuid4
from typing import Literal
import jwt
from os import environ as pyenv
from starlette import status
import datetime as dt
import hashlib

from models import *
import db_manager


access_token_lifetime = 60*30
refresh_token_lifetime = 60*60*24*7
account_app = APIRouter()


async def create_token(types: Literal['access', 'refresh'], payload: dict) -> str:

    # Получаю текущее время для информации о токене
    current_timestamp = dt.datetime.now(tz=dt.timezone.utc).timestamp()

    # Добавляю служебную информацию о токене
    data = {
        'iss': 'account_microservice',  # Кто выдал
        'type': types,  # Тип токена
        'jti': str(uuid4()),  # Уникальный идентификатор
        'nbf': current_timestamp,  # Время создания
        'exp': current_timestamp + refresh_token_lifetime if type == 'refresh' else current_timestamp + access_token_lifetime,  # Время окончания действия
    }

    # Добавляю информацию к пользователю
    payload = payload | data

    # Возвращаю готовый токен
    return str(jwt.encode(payload, pyenv['JWT_SECRET'], algorithm='HS256'))


async def validate_access_token(request: Request):
    try:
        # Получаю токены из куки
        access_token = request.headers.get('jwt_access_token')

        # Если их нет - 401
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Иначе декодирую токен
        payload = jwt.decode(access_token, pyenv['JWT_SECRET'], algorithms=['HS256'])

        # Любой токен кроме аксес будет отклонён
        if payload['type'] != 'access' or payload['iss'] != 'account_microservice':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid token')

        # Проверка если токен просрочен. Если да, запрашиваю его обновление
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= access_token_lifetime:
            raise HTTPException(status_code=status.HTTP_426_UPGRADE_REQUIRED)
        # Если пользователь такого токена есть в бд, то возвращаю "Правда"
        return True
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)


async def update_tokens(token):
    try:
        payload = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])

        # Проверяю, что данный токен - токен обновления
        if payload['type'] != 'refresh':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        # Проверяю, что данный токен существует
        if not await db_manager.validate_refresh_token(hashlib.sha512(token.encode()).hexdigest(), payload):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Проверяю, что данный токен не истёк
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= refresh_token_lifetime:
            # Если существует, удаляю старый токен из БД
            raise HTTPException(status_code=status.HTTP_426_UPGRADE_REQUIRED)
        # Проверяю, что пользователь существует
        if not await db_manager.user_in_db(payload):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        # Получаю два новых токена
        new_access_token = await create_token('access', payload)
        new_refresh_token = await create_token('refresh', payload)
        await db_manager.add_token(hashlib.sha512(new_refresh_token.encode()).hexdigest(), payload)

        await db_manager.delete_token(hashlib.sha512(token.encode()).hexdigest())
        # Возвращаю два новых токена
        return new_access_token, new_refresh_token
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)


async def authorization(token: str, role: list | tuple):
    decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
    user = await db_manager.get_user(decoded_token)
    for user_role in user['roles']:
        if user_role in role:
            return True
    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)


@account_app.post('/api/Authentication/SignUp', status_code=status.HTTP_201_CREATED, response_model=Tokens)
async def sign_up(payload: LoginUser):
    payload = payload.model_dump()
    payload['password'] = hashlib.sha512(payload['password'].encode('utf-8')).hexdigest()
    payload = payload | {'roles': ['User']}
    if not await db_manager.add_user(payload):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
    access_token = await create_token('access', payload)
    refresh_token = await create_token('refresh', payload)
    await db_manager.add_token(hashlib.sha512(refresh_token.encode()).hexdigest(), payload)
    return {'jwt_access_token': access_token, 'jwt_refresh_token': refresh_token}


@account_app.post('/api/Authentication/SignIn', status_code=status.HTTP_200_OK, response_model=Tokens)
async def sign_in(payload: BaseUser):
    payload = payload.model_dump()
    payload['password'] = hashlib.sha512(payload['password'].encode('utf-8')).hexdigest()
    payload = payload | {'roles': ['User']}
    if await db_manager.user_in_db(payload):
        payload = await db_manager.get_user(payload)
        access_token = await create_token('access', payload)
        refresh_token = await create_token('refresh', payload)
        await db_manager.add_token(hashlib.sha512(refresh_token.encode()).hexdigest(), payload)
        return {'jwt_access_token': access_token, 'jwt_refresh_token': refresh_token}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@account_app.put('/api/Authentication/SignOut', status_code=status.HTTP_200_OK)
async def sign_out(request: Request):
    if validate_access_token(request):
        await db_manager.delete_token(hashlib.sha512(request.cookies['jwt_refresh_token'].encode()).hexdigest())


@account_app.get('/api/Authentication/Validate', status_code=status.HTTP_200_OK)
async def validate_token(request: Request):
    if await validate_access_token(request):
        return {'success': True}
    return {'success': False}


@account_app.post('/api/Authentication/Refresh', status_code=status.HTTP_200_OK, response_model=Tokens)
async def refresh(request: Request):
    new_access_token, new_refresh_token = await update_tokens(request.headers.get('jwt_refresh_token'))
    return {'jwt_access_token': new_access_token, 'jwt_refresh_token': new_refresh_token}


@account_app.get('/api/Accounts/Me', status_code=status.HTTP_200_OK, response_model=FullUser)
async def get_info(request: Request):
    if await validate_access_token(request):
        token = request.headers.get('jwt_access_token')
        return await db_manager.get_user(jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256']))


@account_app.put('/api/Accounts/Update', status_code=status.HTTP_200_OK)
async def update(request: Request, payload: UpdateUser):
    if await validate_access_token(request):
        payload = payload.model_dump()
        token = request.cookies.get('jwt_access_token')
        decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        await db_manager.update_user(decoded_token, payload)


@account_app.get('/api/Accounts', status_code=status.HTTP_200_OK)
async def get_accounts(request: Request, start: int = 1, count: int = -1):
    if await validate_access_token(request):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['Admin'])
        finish = []
        if count == -1:
            user_id = 0
            while True:
                user = await db_manager.get_user_by_id(start+user_id)
                if not user:
                    break
                user_id += 1
                if user == 'disabled':
                    continue
                finish.append(user)
        else:
            user_id = 0
            while True:
                user = await db_manager.get_user_by_id(start+user_id)
                if not user:
                    break
                if user == 'disabled':
                    continue
                user_id += 1
                finish.append(user)
                if user_id == count:
                    break
        return {'users': finish}


@account_app.post('/api/Accounts', status_code=status.HTTP_201_CREATED)
async def new_account(request: Request, body: FullUser):
    if validate_access_token(request):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['Admin'])
        payload = body.model_dump()
        payload['password'] = hashlib.sha512(payload['password'].encode('utf-8')).hexdigest()
        if not await db_manager.add_user(payload):
            HTTPException(status.HTTP_400_BAD_REQUEST)


@account_app.put('/api/Accounts/{user_id}', status_code=status.HTTP_200_OK)
async def update_admin(request: Request, body: FullUser, user_id: int):
    if validate_access_token(request):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['Admin'])
        payload = body.model_dump()
        if not await db_manager.update_user_by_id(user_id, payload):
            HTTPException(status.HTTP_404_NOT_FOUND)


@account_app.delete('/api/Accounts/{user_id}', status_code=status.HTTP_200_OK)
async def safe_delete(request: Request, user_id: int):
    if validate_access_token(request):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['Admin'])
        if not await db_manager.soft_delete(user_id):
            HTTPException(status.HTTP_204_NO_CONTENT)

@account_app.get('/api/Doctors/{doctor_id}', status_code=status.HTTP_200_OK)
async def get_doctor(request: Request, doctor_id: int):
    if await validate_access_token(request):
        doctor = await db_manager.get_user_by_id(doctor_id)
        if (not doctor) or ('Doctor' not in doctor['roles']):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        doctor = {'id': doctor_id, 'firstName': doctor['firstName'], 'lastName': doctor['lastName']}
        return doctor

@account_app.get('/api/Doctors', status_code=status.HTTP_200_OK)
async def get_doctors(request: Request, nameFilter: str = ' ', start: int = 0, count: int = -1):
    if await validate_access_token(request):
        finish = await db_manager.get_doctor(start, count, nameFilter)

        return {'doctors': finish}
