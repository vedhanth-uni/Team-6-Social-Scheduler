#refer to the fastapi documentation, especially for databases stuff 

from fastapi import FastAPI

from contextlib import asynccontextmanager

from app.database import engine,init_db

from app import models  # noqa: F401  -- registers all tables before init_db() runs create_all

from app.routers import health # this is how u call an endpoint file from the routers folder, so we're calling health.py in this case
from app.routers import calendars

@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db()
    try:
        yield
    finally:
        engine.dispose()

app = FastAPI(
    title="Social Scheduler API",
    version="0.0.0",
    lifespan=lifespan,
)

@app.get("/")
def default():
    return {"message:" : "Head over to the health page!" }

app.include_router(health.router)
app.include_router(calendars.router)