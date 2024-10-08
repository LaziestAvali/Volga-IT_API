import sqlalchemy as pypg
from databases import Database
from os import environ as pyenv

database_URL = f'postgresql://username:password@127.0.0.1:5432/postgres'

engine = pypg.create_engine(database_URL)
metadata = pypg.MetaData()

account = pypg.Table(
    'account',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True),
    pypg.Column('login', pypg.String(20), nullable=False),
    pypg.Column('password', pypg.String(50), nullable=False),
    pypg.Column('firstName', pypg.String(50), nullable=False),
    pypg.Column('lastName', pypg.String(50), nullable=False)
)

role = pypg.Table(
    'role',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True),
    pypg.Column('name', pypg.String(50), nullable=False),
)

account_role = pypg.Table(
    'account_role',
    metadata,
    pypg.Column('id', pypg.Integer, primary_key=True),
    pypg.Column('account_id', pypg.Integer, nullable=False, foreign_key='user.id'),
    pypg.Column('role_id', pypg.Integer, nullable=False, foreign_key='role.id')

)

database = Database(database_URL)
