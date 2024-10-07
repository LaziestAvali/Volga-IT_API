from fastapi import FastAPI
from contextlib import asynccontextmanager

from Account_microservice.db import metadata, database, engine

from Account_microservice.account import account_app


metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)
app.include_router(account_app)
