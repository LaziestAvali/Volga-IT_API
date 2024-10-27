import sqlalchemy as pypg
from databases import Database
from os import environ as pyenv

database_URL = f"postgresql://{pyenv['TIMETABLE_USER']}:{pyenv['TIMETABLE_PSWD']}@timetable_db:5432/timetable_db"

engine = pypg.create_engine(database_URL)
metadata = pypg.MetaData()

timetables = pypg.Table(
    'timetables',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True, nullable=False),
    pypg.Column('hospitalId', pypg.Integer, nullable=False),
    pypg.Column('doctorId', pypg.Integer, nullable=False),
    pypg.Column('start', pypg.DateTime(timezone=False), nullable=False),
    pypg.Column('to', pypg.DateTime(timezone=False), nullable=False),
    pypg.Column('room', pypg.String(50), nullable=False),
    pypg.Column('is_disabled', pypg.Boolean, nullable=False, default=False)
)

appointment = pypg.Table(
    'appointment',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True, nullable=False),
    pypg.Column('timetable_id', pypg.Integer, nullable=False),
    pypg.Column('account_id', pypg.Integer, nullable=False),
    pypg.Column('time', pypg.DateTime, nullable=False),
    pypg.Column('is_disabled', pypg.DateTime, nullable=False)
)

database = Database(database_URL)
