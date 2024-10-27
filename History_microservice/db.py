import sqlalchemy as pypg
from databases import Database
from os import environ as pyenv

database_URL = f"postgresql://{pyenv['HISTORY_USER']}:{pyenv['HISTORY_PSWD']}@history_db:5432/history_db"

engine = pypg.create_engine(database_URL)
metadata = pypg.MetaData()

histories = pypg.Table(
    'histories',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True, nullable=False),
    pypg.Column('date', pypg.DateTime(timezone=False), nullable=False),
    pypg.Column('pacientId', pypg.Integer, nullable=False),
    pypg.Column('hospitalId', pypg.Integer, nullable=False),
    pypg.Column('doctorId', pypg.Integer, nullable=False),
    pypg.Column('room', pypg.String(50), nullable=False),
    pypg.Column('data', pypg.String(400), nullable=False)
)

database = Database(database_URL)
