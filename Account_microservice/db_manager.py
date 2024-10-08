import sqlalchemy as pypg

from Account_microservice.db import account, role, account_role, database

async def add_user(payload: dict):
    account_id = await database.execute(account.select().where((account.c.login == payload['login']) & account.c.is_disabled == 0))
    if account_id:
        return False
    query = account.insert().values(login=payload['login'], password=payload['password'], firstName=payload['firstName'], lastName=payload['lastName'])
    await database.execute(query=query)
    account_id = await database.execute(account.select().where(account.c.login == payload['login']))
    for user_role in payload['roles']:
        role_id = await database.execute(role.select().where(role.c.name==user_role))
        query = pypg.insert(account_role).values(account_id=account_id, role_id=role_id)
        await database.execute(query=query)
    return True

async def user_in_db(payload: dict):
    is_user_in_db = await database.execute(
            account.select().where(
                (account.c.login == payload['login'])
                & (account.c.password == payload['password'])
                & (account.c.is_disabled == 0)
            )
    )
    if is_user_in_db:
        return True
    return False

async def get_user(payload):
    roles = (
        role.select()
        .select_from(account_role)
        .join(account, account_role.c.account_id == account.c.id)
        .join(role, account_role.c.role_id == role.c.id)
        .where(account.c.login == payload['login'] & account.c.is_disabled == 0)
    )
    roles_list = await database.fetch_all(query=roles)
    for i in range(len(roles_list)):
        roles_list[i] = tuple(roles_list[i].values())[1]
    main_info = await database.fetch_one(query=account.select().where((account.c.login == payload['login']) & (account.c.is_disabled == 0)))
    main_info = tuple(main_info.values())
    main_info = {'login': main_info[1], 'password': main_info[2], 'firstName': main_info[3], 'lastName': main_info[4]}
    full_user = main_info | {'roles': roles_list}
    return full_user


async def get_user_by_id(user_id: int):
    roles = (
        role.select()
        .select_from(account_role)
        .join(account, account_role.c.account_id == account.c.id)
        .join(role, account_role.c.role_id == role.c.id)
        .where((account.c.id == user_id) & (account.c.is_disabled == 0))
    )
    roles_list = await database.fetch_all(query=roles)
    for i in range(len(roles_list)):
        roles_list[i] = tuple(roles_list[i].values())[1]
    main_info = await database.fetch_one(query=account.select().where((account.c.id == user_id) & (account.c.is_disabled == 0)))
    main_info = tuple(main_info.values())
    main_info = {'login': main_info[1], 'password': main_info[2], 'firstName': main_info[3], 'lastName': main_info[4]}
    full_user = main_info | {'roles': roles_list}
    return full_user


async def update_user(payload: dict):
    query = (
        account.update()
        .where((account.c.login == payload['login']) & (account.c.is_disabled == 0))
        .values(firstName=payload['firstName'], lastName=payload['lastName'])
    )
    return await database.execute(query=query)

async def update_user_by_id(user_id: int, payload: dict):
    user = await get_user_by_id(user_id)

    user['password'] = payload['password'] if payload['password'] else user['password']
    user['firstName'] = payload['firstName'] if payload['firstName'] else user['firstName']
    user['lastName'] = payload['lastName'] if payload['lastName'] else user['lastName']
    user_query = (
        pypg.update(account)
        .where(account.c.id == user_id)
        .values(user)
    )
    await database.execute(query=user_query)
