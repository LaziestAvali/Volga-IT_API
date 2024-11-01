import sqlalchemy as pypg

from db import account, tokens, database


async def add_token(token: str, payload: dict):
    user_subquery = account.select().where((account.c.login == payload['login']) & (account.c.is_disabled == False))
    account_id = await database.execute(user_subquery)
    token_query = (
        tokens.insert()
        .values(account_id=account_id, token=token, is_disabled=False)
    )
    await database.execute(query=token_query)


async def validate_refresh_token(token: str, payload: dict):
    query = (
        tokens.select()
        .join(account, tokens.c.account_id == account.c.id)
        .where((account.c.login == payload['login']) & (account.c.is_disabled == False))
    )
    result = await database.fetch_all(query=query)
    for i in range(len(result)):
        result[i] = tuple(result[i].values())[2]
    if token in result:
        return True
    return False


async def delete_token(token: str):
    del_query = (
        tokens.update()
        .where(tokens.c.token == token)
        .values(is_disabled=True)
    )
    await database.execute(query=del_query)


async def add_user(payload: dict):
    account_id = await database.fetch_one(account.select().where((account.c.login == payload['login']) & (account.c.is_disabled == False)))
    if account_id:
        return False
    query = account.insert().values(login=payload['login'], password=payload['password'], firstName=payload['firstName'], lastName=payload['lastName'], roles=tuple(payload['roles']),  is_disabled=False)
    await database.execute(query=query)
    return True


async def user_in_db(payload: dict):
    is_user_in_db = await database.execute(
            account.select().where(
                (account.c.login == payload['login'])
                & (account.c.password == payload['password'])
                & (account.c.is_disabled == False)
            )
    )
    if is_user_in_db:
        return True
    return False


async def get_user(payload: dict):
    main_info = await database.fetch_one(query=account.select().where((account.c.login == payload['login']) & (account.c.is_disabled == False)))
    main_info = tuple(main_info.values())[:6]
    main_info = {'id':main_info[0], 'login': main_info[1], 'password': main_info[2], 'firstName': main_info[3], 'lastName': main_info[4], 'roles': list(main_info[5])}
    return main_info


async def get_doctor(start: int, count: int, name_filter: str):
    full_name = account.c.firstName + ' ' + account.c.lastName
    doctor_subquery = (
        account.select()
        .where((account.c.roles.contains(['Doctor'])) & (account.c.is_disabled == False) & (full_name.icontains(name_filter)))
        .order_by(account.c.id)
        .subquery()
    )
    doctor_query = (
        pypg.select(doctor_subquery).offset(start)
    )
    if count >= -1:
        doctor_query = doctor_query.limit(count)
    doctor_list = await database.fetch_all(query=doctor_query)
    for i in range(len(doctor_list)):
        temp = tuple(doctor_list[i].values())
        doctor_list[i] = tuple([temp[0], temp[3], temp[4]])
    return doctor_list


async def get_user_by_id(user_id: int):
    main_info = await database.fetch_one(
        query=account.select().where(account.c.id == user_id))
    if not main_info:
        return False
    main_info = tuple(main_info.values())
    if main_info[-1]:
        return 'disabled'
    main_info = {'login': main_info[1], 'password': main_info[2], 'firstName': main_info[3], 'lastName': main_info[4], 'roles': list(main_info[5])}
    return main_info


async def update_user(token: dict, payload: dict):
    user = await get_user(token)
    if not user:
        return False
    user['password'] = payload['password'] if payload['password'] else user['password']
    user['firstName'] = payload['firstName'] if payload['firstName'] else user['firstName']
    user['lastName'] = payload['lastName'] if payload['lastName'] else user['lastName']
    query = (
        account.update()
        .where((account.c.login == user['login']) & (account.c.is_disabled == False))
        .values(password=user['password'], firstName=user['firstName'], lastName=user['lastName'])
    )
    await database.execute(query=query)
    return True


async def update_user_by_id(user_id: int, payload: dict):
    user = await get_user_by_id(user_id)
    if not user:
        return False
    user['login'] = payload['login'] if payload['login'] else user['login']
    user['password'] = payload['password'] if payload['password'] else user['password']
    user['firstName'] = payload['firstName'] if payload['firstName'] else user['firstName']
    user['lastName'] = payload['lastName'] if payload['lastName'] else user['lastName']
    user['roles'] = payload['roles'] if payload['roles'] else user['roles']
    user_query = (
        account.update()
        .where(account.c.id == user_id)
        .values(user)
    )
    database.execute(query=user_query)
    return True


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
        .values(is_disabled=True)
    )
    await database.execute(query=del_query)
    return True
