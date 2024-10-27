import sqlalchemy as pypg
from datetime import datetime

from db import database, timetables, appointment


async def new_timetable(payload: dict):
    query = (
        timetables.insert()
        .values(hospitalId=payload['hospitalId'], doctorId=payload['doctorId'], start=payload['start'], to=payload['to'], room=payload['room'], is_disabled=False)
    )
    await database.execute(query=query)

async def update_timetable(payload: dict, timetable_id: int):
    query = (
        timetables.select()
        .where((timetables.c.id == timetable_id) & (timetables.c.is_disabled == False))
    )
    timetable = await database.fetch_one(query=query)
    if not timetable:
        return False
    timetable = list(timetable.values())
    timetable[1] = payload['hospitalId'] if payload['hospitalId'] else timetable[1]
    timetable[2] = payload['doctorId'] if payload['doctorId'] else timetable[2]
    timetable[3] = payload['start'] if payload['start'] else timetable[3]
    timetable[4] = payload['to'] if payload['to'] else timetable[4]
    timetable[5] = payload['room'] if payload['room'] else timetable[5]
    update_query = (
        timetables.update()
        .where(timetables.c.id == timetable_id)
        .values(timetable[:])
    )
    await database.execute(query=update_query)
    return True

async def get_timetable_of_hospital(payload: dict, hospital_id: int):
    query = (
        timetables.select()
        .where((timetables.c.hospitalId == hospital_id) & (timetables.c.start <= payload['start']) & (timetables.c.to <= payload['to']) & (timetables.c.is_disabled == False))
    )
    data = await database.fetch_all(query=query)
    for i in range(len(data)):
        data[i] = tuple(data[i].values())[:6]
    return data

async def get_timetable_of_doctor(payload: dict, doctor_id: int):
    query = (
        timetables.select()
        .where((timetables.c.doctorId == doctor_id) & (timetables.c.start <= payload['start']) & (timetables.c.to <= payload['to']) & (timetables.c.is_disabled == False))
    )
    data = await database.fetch_all(query=query)
    for i in range(len(data)):
        data[i] = tuple(data[i].values())[:6]
    return data

async def get_timetable_of_room(payload: dict, hospital_id: int, room_name: str):
    query = (
        timetables.select()
        .where((timetables.c.hospitalId == hospital_id) & (timetables.c.start <= payload['start'])
               & (timetables.c.to <= payload['to']) & (timetables.c.room == room_name)
               & (timetables.c.is_disabled == False))
    )
    data = await database.fetch_all(query=query)
    for i in range(len(data)):
        data[i] = tuple(data[i].values())[:6]
    return data

async def get_timetable_by_id(timetable_id: int):
    query = (
        timetables.select()
        .where(timetables.c.id == timetable_id)
    )
    timetable = await database.fetch_one(query=query)
    timetable = list(timetable.values())
    return timetable

async def delete_timetable(timetable_id: int):
    timetable = await get_timetable_by_id(timetable_id)
    if not timetable:
        return False
    del_query = (
        timetables.update()
        .where(timetables.c.id == timetable_id)
        .values(is_disabled=True)
    )
    await database.execute(query=del_query)
    return True

async def delete_by_doctor(doctor_id: int):
    query = (
        timetables.select()
        .where(timetables.c.doctorId == doctor_id)
    )
    timetable = await database.fetch_one(query=query)
    timetable = list(timetable.values())
    if not timetable:
        return False
    del_query = (
        timetables.update()
        .where(timetables.c.doctorId == doctor_id)
        .values(is_disabled=True)
    )
    await database.execute(query=del_query)
    return True

async def delete_by_hospital(hospital_id: int):
    query = (
        timetables.select()
        .where(timetables.c.hospitaId == hospital_id)
    )
    timetable = await database.fetch_one(query=query)
    timetable = list(timetable.values())
    if not timetable:
        return False
    del_query = (
        timetables.update()
        .where(timetables.c.hospitaId == hospital_id)
        .values(is_disabled=True)
    )
    await database.execute(query=del_query)
    return True

async def new_appointment(timetable_id: int, account_id: int, time: datetime):
    query = (
        appointment.insert()
        .values(timetable_id=timetable_id, account_id=account_id, time=time, is_disabled=False)
    )
    given_id = await database.execute(query=query)
    return given_id

async def get_appointments_of_timetable(timetable_id: int):
    query = (
        appointment.select()
        .where((appointment.c.timetable_id == timetable_id) & (appointment.c.is_disabled == False))
    )
    result = await database.fetch_one(query=query)
    if result is None:
        return False
    return tuple(result.values())

async def get_appointment_by_id(appointment_id:int):
    query = (
        appointment.select()
        .where((appointment.c.id == appointment_id) & (appointment.c.is_disabled == False))
    )
    result = await database.fetch_all(query=query)
    return tuple(result.values())

async def delete_appointment(appointment_id: int):
    query = (
        appointment.update()
        .where(appointment.c.id == appointment_id)
    )
    await database.execute(query=query)
