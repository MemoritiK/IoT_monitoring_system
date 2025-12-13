from fastapi import FastAPI
from contextlib import asynccontextmanager
from modules import time_series, devices
from database_sql import create_db_and_tables
from database_influx import init_inlfux
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.write_api, app.state.query_api = init_inlfux()
    create_db_and_tables()
    yield 

app = FastAPI(lifespan=lifespan)
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

@app.get("/", response_class=HTMLResponse)
def serve_home():
    index_path = Path("templates/index.html")
    return index_path.read_text()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)


app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(time_series.router, prefix="/data", tags=["data"])
