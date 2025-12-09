from fastapi import FastAPI
from contextlib import asynccontextmanager
from modules import devices
from database import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables before app starts
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(devices.router, prefix="/devicess", tags=["devices"])
