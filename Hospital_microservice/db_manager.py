import sqlalchemy as pypg

from db import hospitals, rooms, database


async def get_all_hospital(start: int, count: int):
    hospitals_subquery = hospitals.select().where(hospitals.c.is_disabled == 0).subquery()
    hospitals_query = pypg.select(hospitals_subquery).offset(start)
    if count != -1:
        hospitals_query = hospitals_query.limit(count)
    hospitals_list = await database.fetch_all(hospitals_query)
    for i in hospitals_list:
        hospitals_list[i] = tuple(hospitals_list[i].values())[:2]
    return hospitals_list


async def get_hospital_id(hospital_id: int):
    query = hospitals.select().where((hospitals.c.id == hospital_id) & (hospitals.c.is_disabled == 0))
    hospital_list = await database.fetch_one(query)
    return tuple(hospital_list.values())


async def get_hospital_rooms(hospital_id: int):
    query = (
        rooms.select()
        .join(hospitals, rooms.c.hospital_id == hospitals.c.id)
        .where((hospitals.c.id == hospital_id) & (hospitals.c.is_disabled == False))
    )
    room_tuple = await database.fetch_all(query)
    for i in range(len(room_tuple)):
        room_tuple[i] = tuple(room_tuple[i].values())[2]
    return room_tuple


async def add_hospital(payload: dict):
    query = (
        hospitals.insert()
        .values(name=payload['name'], address=payload['address'], contactPhone=payload['contactPhone'], is_disabled=False)
    )
    await database.execute(query=query)
    return True