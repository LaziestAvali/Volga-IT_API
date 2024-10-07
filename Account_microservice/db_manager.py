from fastapi import HTTPException
from starlette import status
import sqlalchemy as pypg

from Account_microservice.models import BaseUser, LoginUser, FullUser
from Account_microservice.db import account, role, account_role, database

async def add_user(payload):
    if type(payload) == FullUser:
        payload = payload.model_dump()
    account_id = await database.execute(account.select().where(account.c.login == payload['login']))
    if account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
    query = account.insert().values(login=payload['login'], password=payload['password'], firstName=payload['firstName'], lastName=payload['lastName'])
    await database.execute(query=query)
    account_id = await database.execute(account.select().where(account.c.login == payload['login']))
    for user_role in payload['roles']:
        role_id = await database.execute(role.select().where(role.c.name==user_role))
        query = pypg.insert(account_role).values(account_id=account_id, role_id=role_id)
        await database.execute(query=query)

async def user_in_db(payload):
    if type(payload) != dict:
        payload = payload.model_dump()
    if await database.execute(account.select().where((account.c.login == payload['login']) & (account.c.password == payload['password']))):
        return True
    return False

async def get_user(payload):
    print(payload['login'])
    roles = (
        role.select()
        .select_from(account_role)
        .join(account, account_role.c.account_id == account.c.id)
        .join(role, account_role.c.role_id == role.c.id)
        .where(account.c.login == payload['login'])
    )
    print(roles)
    roles_list = await database.fetch_all(query=roles)
    for i in range(len(roles_list)):
        roles_list[i] = tuple(roles_list[i].values())
        print(roles_list[i])
    print('roles_list: ' + str(roles_list))
    main_info = await database.fetch_one(query=account.select().where(account.c.login==payload['login']))
    print(main_info.__dict__)
    full_user = main_info | {roles: roles_list}

    return full_user

async def update_user(payload: LoginUser):
    query = account.update().where(account.c.login==payload['login']).values(firstName=payload['firstName'], lastName=payload['lastName'])
    return await database.execute(query=query)
