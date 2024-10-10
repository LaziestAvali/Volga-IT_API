import sqlalchemy as pypg

from Account_microservice.db import account, role, account_role, tokens, database

## ТЕСТИТЬ
async def add_token(token: str, payload: dict):
    user_subquery = account.select().where((account.c.login == payload['login']) & account.c.is_disabled == 0).subquery()
    token_query = (
        tokens.insert()
        .values(tokens.c.account_id.in_(user_subquery), token=token)
    )
    await database.execute(query=token_query)

## ТЕСТИТЬ
async def validate_refresh_token(token: str, payload: dict):
    query = (
        tokens.select()
        .join(account, tokens.c.account_id == account.c.id)
        .where(account.c.login == payload['login'])
    )
    result = await database.fetch_all(query=query)
    for i in range(len(result)):
        result[i] = tuple(result[i].values())[2]
    if token in result:
        return True
    return False

## ТЕСТИТЬ
async def delete_token(token: str):
    query = (
        tokens.delete().where(tokens.c.token == token)
    )
    await database.execute(query=query)


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


async def get_user(payload: dict):
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


async def get_doctor(payload: dict):
    doctor_query = (
        account.select()
        .select_from(account_role)
        .join(account, account_role.c.account_id == account.c.id)
        .join(role, account_role.c.role_id == role.c.id)
        .where((role.c.name == 'doctor') & (account.c.is_disabled == 0) & ((account.c.firstName + account.c.lastName).icontains(payload['nameFilter'])))
    )


async def get_user_by_id(user_id: int):
    main_info = await database.fetch_one(
        query=account.select().where((account.c.id == user_id) & (account.c.is_disabled == 0)))
    main_info = tuple(main_info.values())
    if not main_info:
        return False
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

    main_info = {'login': main_info[1], 'password': main_info[2], 'firstName': main_info[3], 'lastName': main_info[4]}
    full_user = main_info | {'roles': roles_list}
    return full_user

## ТЕСТИТЬ
async def update_user(payload: dict):
    query = (
        account.update()
        .where((account.c.login == payload['login']) & (account.c.is_disabled == 0))
        .values(firstName=payload['firstName'], lastName=payload['lastName'])
    )
    return await database.execute(query=query)

## ТЕСТИТЬ
async def update_user_by_id(user_id: int, payload: dict):
    user = await get_user_by_id(user_id)
    if not user:
        return False
    user['login'] = payload['login'] if payload['login'] else user['login']
    user['password'] = payload['password'] if payload['password'] else user['password']
    user['firstName'] = payload['firstName'] if payload['firstName'] else user['firstName']
    user['lastName'] = payload['lastName'] if payload['lastName'] else user['lastName']
    user_query = (
        account.update()
        .where(account.c.id == user_id)
        .values(user)
    )
    updated_user_id = await database.execute(query=user_query)
    account_role_del_query = (
        account_role.delete()
        .where(account_role.c.account_id == updated_user_id)
    )
    await database.execute(query=account_role_del_query)
    for user_role in payload['roles']:
        role_id = await database.execute(role.select().where(role.c.name==user_role))
        query = pypg.insert(account_role).values(account_id=updated_user_id, role_id=role_id)
        await database.execute(query=query)

    return True

## ТЕСТИТЬ
async def soft_delete(user_id: int):
    user_real = (
        account.select()
        .where(account.c.id == user_id)
    )
    if not await database.execute(query=user_real):
        return False
    del_query = (
        account.update()
        .where(account.c.id == user_id)
        .values(is_disabled=1)
    )
    await database.execute(query=del_query)
    return True
