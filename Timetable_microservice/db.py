import sqlalchemy as pypg
from databases import Database
from os import environ as pyenv

database_URL = f"dbURI"

engine = pypg.create_engine(database_URL)
metadata = pypg.MetaData()

timetables = pypg.Table(
    'timetables',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True, nullable=False),
    pypg.Column('hospitalId', pypg.Integer, nullable=False),
    pypg.Column('doctorId', pypg.Integer, nullable=False),
    pypg.Column('start', pypg.DateTime, nullable=False),
    pypg.Column('to', pypg.DateTime, nullable=False),
    pypg.Column('room', pypg.String(50), nullable=False),
    pypg.Column('is_deleted', pypg.Boolean, nullable=False, default=False)
)

appointment = pypg.Table(
    'appointment',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True, nullable=False),
    pypg.Column('timetable_id', pypg.Integer, nullable=False),
    pypg.Column('account_id', pypg.Integer, nullable=False),
    pypg.Column('time', pypg.DateTime, nullable=False)
)

database = Database(database_URL)
