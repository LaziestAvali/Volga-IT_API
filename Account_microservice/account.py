from fastapi import APIRouter, HTTPException, Request, Response

from uuid import uuid4
from typing import Literal
import jwt
from os import environ as pyenv
from starlette import status
import datetime as dt
import hashlib


from Account_microservice.models import BaseUser, LoginUser, UpdateUser, FullUser, UserIds, DoctorIds
from Account_microservice import db_manager


access_token_lifetime = 60*10
refresh_token_lifetime = 60*60*24*7
account_app = APIRouter()


async def create_token(types: Literal['access', 'refresh'], payload: dict) -> str:

    # Получаю текущее время для информации о токене
    current_timestamp = dt.datetime.now(tz=dt.timezone.utc).timestamp()

    # Добавляю служебную информацию о токене
    data = {
        'iss': 'account_microservice',  # Кто выдал
        'type': types,  # Тип токена
        'jti': uuid4(),  # Уникальный идентификатор
        'nbf': current_timestamp,  # Время создания
        'exp': current_timestamp + refresh_token_lifetime if type == 'refresh' else current_timestamp + access_token_lifetime,  # Время окончания действия
    }

    # Добавляю информацию к пользователю
    payload = payload | data

    # Возвращаю готовый токен
    return str(jwt.encode(payload, pyenv['JWT_SECRET'], algorithm='HS256'))


async def validate_access_token(request: Request, response: Response) -> bool:
    try:
        # Получаю токены из куки
        access_token = request.cookies.get('jwt_access_token')

        # Если их нет - 401
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Иначе декодирую токен
        payload = jwt.decode(access_token, pyenv['JWT_SECRET'], algorithms=['HS256'])

        # Любой токен кроме аксес будет отклонён
        if payload['type'] != 'access':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid token')

        # Проверка если токен просрочен. Если да, запрашиваю его обновление
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= access_token_lifetime:
            refresh_token = request.cookies.get('jwt_refresh_token')
            new_access_token, new_refresh_token = await update_tokens(refresh_token)
            response.set_cookie('jwt_access_token', new_access_token)
            response.set_cookie('jwt_refresh_token', new_refresh_token)
        # Если пользователь такого токена есть в бд, то возвращаю "Правда"
        if await db_manager.user_in_db(payload):
            return True
        return False
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

        # Если существует, удаляю старый токен из БД
        await db_manager.delete_token(hashlib.sha512(token.encode()).hexdigest())

        # Проверяю, что данный токен не истёк
        if payload['nbf'] - dt.datetime.now(tz=dt.timezone.utc).timestamp() >= refresh_token_lifetime:
            raise HTTPException(status_code=status.HTTP_426_UPGRADE_REQUIRED)

        # Получаю два новых токена
        new_access_token = await create_token('access', payload)
        new_refresh_token = await create_token('refresh', payload)

        # Добавляю новый токен обновления в БД
        await db_manager.add_token(hashlib.sha512(new_refresh_token.encode()).hexdigest(), payload)

        # Возвращаю два новых токена
        return new_access_token, new_refresh_token
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)


async def authorization(token: str, role: list | tuple):
    decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
    user = await db_manager.get_user(decoded_token)
    for user_role in user['roles']:
        if user_role in role:
            return
    raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)


@account_app.post('/api/Authentication/SignUp')
async def sign_up(response: Response, payload: LoginUser):
    payload = payload.model_dump()
    payload['password'] = hashlib.sha512(payload['password'].encode('utf-8')).hexdigest()
    payload = payload | {'roles': ['user']}
    if not await db_manager.add_user(payload):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
    response.set_cookie(key='jwt_access_token', value=await create_token('access', payload), httponly=True)
    refresh_token = await create_token('refresh', payload)
    await db_manager.add_token(hashlib.sha512(refresh_token.encode()).hexdigest(), payload)
    response.set_cookie(key='jwt_refresh_token', value=refresh_token, httponly=True)


@account_app.post('/api/Authentication/SignIn', status_code=status.HTTP_200_OK)
async def sign_in(response: Response, payload: BaseUser):
    payload = payload.model_dump()
    payload['password'] = hashlib.sha512(payload['password'].encode('utf-8')).hexdigest()
    payload = payload | {'roles': ['user']}
    if await db_manager.user_in_db(payload):
        payload = await db_manager.get_user(payload)
        response.set_cookie(key='jwt_access_token', value=await create_token('access', payload), httponly=True)
        refresh_token = await create_token('refresh', payload)
        await db_manager.add_token(hashlib.sha512(refresh_token.encode()).hexdigest(), payload)
        response.set_cookie(key='jwt_refresh_token', value=refresh_token, httponly=True)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@account_app.put('/api/Authentication/SignOut', status_code=status.HTTP_200_OK)
async def sign_out(request: Request, response: Response):
    if validate_access_token(request, response):
        response.delete_cookie(key='jwt_access_token')
        response.delete_cookie(key='jwt_refresh_token')


@account_app.get('/api/Authentication/Validate', status_code=status.HTTP_200_OK)
async def validate(request: Request, response: Response):
    if await validate_access_token(request, response):
        return {'success': True}
    return {'success': False}


@account_app.post('/api/Authentication/Refresh', status_code=status.HTTP_200_OK)
async def refresh(request: Request, response: Response):
    new_access_token, new_refresh_token = await update_tokens(request.cookies.get('jwt_refresh_token'))
    response.set_cookie(key='jwt_access_token', value=new_access_token, httponly=True)
    response.set_cookie(key='jwt_refresh_token', value=new_refresh_token, httponly=True)


@account_app.get('/api/Accounts/Me', status_code=status.HTTP_200_OK)
async def get_info(request: Request, response: Response):
    if await validate_access_token(request, response):
        token = request.cookies.get('jwt_access_token')
        return await db_manager.get_user(jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256']))


@account_app.put('/api/Accounts/Update', status_code=status.HTTP_200_OK)
async def update(request: Request, response: Response, payload: UpdateUser):
    if await validate_access_token(request, response):
        token = request.cookies.get('jwt_access_token')
        decoded_token = jwt.decode(token, pyenv['JWT_SECRET'], algorithms=['HS256'])
        payload = payload.model_dump()
        await db_manager.update_user(decoded_token)


@account_app.get('/api/Accounts', status_code=status.HTTP_200_OK)
async def get_accounts(request: Request, response: Response, body: UserIds):
    if await validate_access_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['admin'])
        payload = body.model_dump()
        finish = []
        start = int(payload['start'])
        for account in range(payload['count']):
            user = await db_manager.get_user_by_id(start+account)
            if user:
                finish.append(user)
                continue
            raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
        return {'users': finish}


@account_app.post('/api/Accounts', status_code=status.HTTP_201_CREATED)
async def new_account(request: Request, response: Response, body: FullUser):
    if validate_access_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['admin'])
        if not await db_manager.add_user(body.model_dump()):
            HTTPException(status.HTTP_404_NOT_FOUND)


@account_app.put('/api/Accounts/{user_id}')
async def update_admin(request: Request, response: Response, body: FullUser, user_id: int):
    if validate_access_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['admin'])
        payload = body.model_dump()
        if not await db_manager.update_user_by_id(user_id, payload):
            HTTPException(status.HTTP_404_NOT_FOUND)


@account_app.delete('/api/Accounts/{user_id}')
async def safe_delete(request: Request, response: Response, user_id: int):
    if validate_access_token(request, response):
        token = request.cookies.get('jwt_access_token')
        await authorization(token, ['admin'])
        if not await db_manager.soft_delete(user_id):
            HTTPException(status.HTTP_404_NOT_FOUND)


@account_app.get('/api/Doctors')
async def get_doctors(request: Request, response: Response, doctor_id: DoctorIds):
    if validate_access_token(request, response):
        doctor_id = doctor_id.model_dump()
        user = db_manager.get_doctor(doctor_id)
