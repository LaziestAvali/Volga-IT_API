from db import database, histories

async def get_short_histories(pacientId):
    query =(
        histories.select()
        .where(histories.c.pacientId == pacientId)
    )
    raw_list = await database.fetch_all(query)
    for i in range(len(raw_list)):
        raw_list[i] = tuple(raw_list[i].values())[:2]
    return raw_list

async def get_history_id(history_id):
    query = (
        histories.select()
        .where(histories.c.id == history_id)
    )
    raw_list = await database.fetch_one(query)
    if not raw_list:
        return False
    return tuple(raw_list[0].values())

async def new_history(payload: dict):
    query = (
        histories.insert()
        .values(date=payload['date'], pacientId=payload['pacientId'], hospitalId=payload['hospitalId'], doctorId=payload['doctorId'], room=payload['room'], data=payload['data'])
    )
    that_id = await database.execute(query)
    return that_id

async def update_history(history_id: int, payload: dict):
    history = list(await get_history_id(history_id))
    if not history:
        return False
    history[1] = payload['date'] if payload['date'] else history[1]
    history[2] = payload['pacientId'] if payload['pacientId'] else history[2]
    history[3] = payload['hospitalId'] if payload['hospitalId'] else history[3]
    history[4] = payload['doctorId'] if payload['doctorId'] else history[3]
    history[5] = payload['room'] if payload['room'] else history[4]
    history[6] = payload['data'] if payload['data'] else history[5]
    update_query = (
        histories.update()
        .where(histories.c.id == history_id)
        .values(history[:])
    )
    await database.execute(query=update_query)
    return True


