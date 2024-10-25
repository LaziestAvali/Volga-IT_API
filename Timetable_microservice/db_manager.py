import sqlalchemy as pypg

from db import database, timetables, appointment


async def new_timetable(payload: dict):
    query = (
        timetables.insert()
        .values(hospitalId=payload['hospitalId'], doctorId=payload['doctorId'], start=payload['start'], to=payload['to'], is_disabled=False)
    )
    database.execute(query=query)

async def update_timetable(payload: dict):
    pass