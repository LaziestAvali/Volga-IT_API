import sqlalchemy as pypg

from db import hospitals, database


async def get_all_hospital(start: int, count: int):
    hospitals_subquery = hospitals.select().where(hospitals.c.is_disabled == False).subquery()
    hospitals_query = pypg.select(hospitals_subquery).offset(start)
    if count > -1:
        hospitals_query = hospitals_query.limit(count)
    hospitals_list = await database.fetch_all(hospitals_query)
    for i in range(len(hospitals_list)):
        raw_data = tuple(hospitals_list[i].values())
        hospitals_list[i] = {'id': raw_data[0], 'name': raw_data[1]}
    return tuple(hospitals_list)


async def get_hospital_id(hospital_id: int):
    query = hospitals.select().where((hospitals.c.id == hospital_id) & (hospitals.c.is_disabled == False))
    hospital_list = await database.fetch_one(query)
    return tuple(hospital_list.values())[1:4]


async def get_hospital_rooms(hospital_id: int):
    query = (
        hospitals.select()
        .where((hospitals.c.id == hospital_id) & (hospitals.c.is_disabled == False))
    )
    room_tuple = await database.fetch_all(query)
    for i in range(len(room_tuple)):
        room_tuple[i] = tuple(room_tuple[i].values())[4]
    return room_tuple[0]


async def add_hospital(payload: dict):
    query = (
        hospitals.insert()
        .values(name=payload['name'], address=payload['address'], contactPhone=payload['contactPhone'], rooms=payload['rooms'], is_disabled=False)
    )
    await database.execute(query=query)
    return True


async def update_hospital(hospital_id: int, payload: dict):
    updating_hospital = list(await get_hospital_id(hospital_id))
    if not updating_hospital:
        return False
    updating_hospital[1] = payload['name'] if payload['name'] is not None else updating_hospital[1]
    updating_hospital[2] = payload['address'] if payload['address'] is not None else updating_hospital[2]
    updating_hospital[3] = payload['contactPhone'] if payload['contactPhone'] is not None else updating_hospital[3]
    updating_hospital[4] = payload['rooms'] if payload['rooms'] is not None else updating_hospital[4]
    hospital_query = (
        hospitals.update()
        .where(hospitals.c.id == hospital_id)
        .values(updating_hospital[1:5])
    )
    await database.execute(query=hospital_query)
    return True


async def soft_delete(hospital_id):
    hospital_real = await get_hospital_id(hospital_id)
    if not hospital_real:
        return False
    del_query = (
        hospitals.update
        .where(hospitals.c.id == hospital_id)
        .values(is_disabled=True)
    )
    await database.execute(del_query)
    return True
