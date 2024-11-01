import sqlalchemy as pypg
from databases import Database
from os import environ as pyenv

database_URL = f"postgresql://{pyenv['HOSPITAL_USER']}:{pyenv['HOSPITAL_PSWD']}@hospital_db:5432/hospital_db"

engine = pypg.create_engine(database_URL)
metadata = pypg.MetaData()

hospitals = pypg.Table(
    'hospitals',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True, nullable=False),
    pypg.Column('name', pypg.String(50), nullable=False),
    pypg.Column('address', pypg.String(100), nullable=False),
    pypg.Column('contactPhone', pypg.String(20), nullable=False),
    pypg.Column('rooms', pypg.ARRAY(pypg.String(50)), nullable=False),
    pypg.Column('is_disabled', pypg.Boolean, nullable=False, default=False)
)

database = Database(database_URL)
