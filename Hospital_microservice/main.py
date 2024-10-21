from fastapi import FastAPI
from contextlib import asynccontextmanager

from db import metadata, database, engine

from hospital import hospital_app


metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)
app.include_router(hospital_app)
